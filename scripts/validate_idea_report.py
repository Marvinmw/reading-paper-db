#!/usr/bin/env python3
"""Validate an idea report against the methodology hard constraints.

Usage:
    python3 scripts/validate_idea_report.py <report.json>
    python3 scripts/validate_idea_report.py output/reports/report_*.json

Exit code: 0 if all pass, 1 if any constraint violated.
"""
from __future__ import annotations
import json, sys, re, glob
from pathlib import Path
from collections import Counter

# ── enum sets per idea-generation-method.md
STRATEGY = {'phenomenon_discovery','assumption_break','ecosystem_distortion',
            'hidden_failure_mode','new_problem_class','better_solution'}
FTYPE   = {'hypothesis','research_question','proposed_construct'}
NTYPE   = {'unsolved_problem','research_gap','better_solution'}
METHOD  = {'empirical_study','technical_contribution','theoretical','vision_position'}
CFORM   = {'new_problem','new_solution','better_solution'}
FALLACY = {'confirmation_bias','hasty_generalization','cherry_picking',
           'survivorship_bias','ecological_fallacy','none'}
PRISK   = {'high','medium','low'}
DOMAIN_TAGS = {
    'database',
    'distributed_systems',
    'web3',
    'network',
    'security',
    'programming_languages',
}

NUM_PAT = re.compile(r'\d+\s*%|\d+\s*pp|[≥≤><]=?\s*\d|=\s*\d+\.\d|r\s*[<>≤≥]=?\s*\d')
JARGON  = ['范式失效','系统性失效','SOTA','paradigm-level','separation 范式',
           'contextual manipulation']

def check_idea(item, label):
    """Return list of failure messages for one idea."""
    fails = []
    title = item.get('title','<no-title>')
    p = lambda msg: fails.append(f'[{label}] {title}: {msg}')

    # 1. 5 大字段 + scoring 全填
    for k in ['idea','motivation','novelty','feasibility','evaluation',
              'finer','stress_test','ai_failure_mode_check']:
        if k not in item:
            p(f'missing {k}')

    # 2. strategy enum
    if item.get('strategy') not in STRATEGY:
        p(f'bad strategy: {item.get("strategy")}')

    # Domain relevance schema (new DB/Web3/distributed project schema)
    tags = item.get('domain_tags', [])
    if not tags and not item.get('is_se_related'):
        p('missing domain_tags')
    if tags:
        if not isinstance(tags, list):
            p('domain_tags must be a list')
        else:
            bad_tags = [t for t in tags if t not in DOMAIN_TAGS]
            if bad_tags:
                p(f'bad domain_tags: {bad_tags}')

    # 3. idea: 3 enums + one_liner + approach
    idea = item.get('idea', {})
    if idea.get('formulation_type') not in FTYPE:
        p(f'bad formulation_type: {idea.get("formulation_type")}')
    if idea.get('method_type') not in METHOD:
        p(f'bad method_type: {idea.get("method_type")}')
    if idea.get('contribution_form') not in CFORM:
        p(f'bad contribution_form: {idea.get("contribution_form")}')

    ol = idea.get('one_liner','')
    if not ol:
        p('no one_liner')
    elif len(ol) > 35:
        p(f'one_liner too long: {len(ol)} chars (max 35)')
    elif ol.count('。') > 1 or '——' in ol or '；' in ol:
        p(f'one_liner not single sentence')
    if NUM_PAT.search(ol):
        p(f'one_liner contains predicted number: "{NUM_PAT.search(ol).group()}"')
    for j in JARGON:
        if j in ol:
            p(f'one_liner contains jargon: "{j}"')

    if not idea.get('approach'):
        p('no approach')

    # 4. motivation: signal + why_matters
    mot = item.get('motivation', {})
    if not mot.get('why_matters'):
        p('no motivation.why_matters')
    sig = mot.get('signal', {})
    if not sig.get('summary') or not sig.get('source_papers'):
        p('incomplete motivation.signal')

    # 5. novelty: ≥1 closest_prior_work with concrete what_they_did / what_we_dont_do
    nv = item.get('novelty', {})
    if nv.get('novelty_type') not in NTYPE:
        p(f'bad novelty_type: {nv.get("novelty_type")}')
    cpw = nv.get('closest_prior_work', [])
    if len(cpw) < 1:
        p('novelty.closest_prior_work empty')
    for w in cpw:
        if not w.get('what_they_did') or not w.get('what_we_dont_do'):
            p(f'prior_work entry missing what_they_did/what_we_dont_do')

    # 6. feasibility
    feas = item.get('feasibility', {})
    for k in ['data_source','effort_estimate','key_risks']:
        if not feas.get(k):
            p(f'feasibility missing {k}')

    # 7. evaluation
    ev = item.get('evaluation', {})
    if not ev.get('expected_findings'):
        p('evaluation missing expected_findings')
    if not ev.get('null_result'):
        p('evaluation missing null_result')

    # 8. FINER avg ≥ 3.0, all ≥ 2
    fnr = item.get('finer', {})
    try:
        scores = [fnr.get(k) for k in ['feasible','interesting','novel','ethical','relevant']]
        if any(s is None or s < 2 for s in scores):
            p(f'FINER 单项 < 2: {scores}')
        avg = float(fnr.get('average', 0))
        if avg < 3.0:
            p(f'FINER avg < 3.0: {avg}')
    except (ValueError, TypeError):
        p('FINER 评分非数值')

    # 9. stress_test
    st = item.get('stress_test', {})
    for k in ['strongest_counter','biggest_confound']:
        if not st.get(k):
            p(f'stress_test missing {k}')
    if st.get('fallacy_risk') not in FALLACY:
        p(f'bad fallacy_risk: {st.get("fallacy_risk")}')
    if st.get('preprint_risk') not in PRISK:
        p(f'bad preprint_risk: {st.get("preprint_risk")}')
    if st.get('preprint_risk') == 'high':
        reason = st.get('preprint_risk_reason','')
        if not any(k in reason.lower() for k in ['降级','reframe','paradigm','synthesis','vision']):
            p(f'preprint_risk=high without reframe path in reason')

    # 10. ai_failure_mode_check
    a = item.get('ai_failure_mode_check', {})
    fl = a.get('frame_lock','')
    if not fl or fl.strip() == 'N/A':
        p('frame_lock required (≥1 alternative framing)')

    # 11. better_solution must have L + I numbers
    if idea.get('contribution_form') == 'better_solution':
        ef = ev.get('expected_findings','')
        if not NUM_PAT.search(ef):
            p('better_solution: expected_findings 缺数值 (L 或 I)')

    return fails


def check_report(rep):
    """Return list of report-level failure messages."""
    fails = []

    # Get ideas (new schema uses single `ideas`; legacy uses two lists)
    ideas = rep.get('ideas')
    if ideas is None:
        # backward compat: merge old structure
        ideas = (rep.get('research_opportunities', []) +
                 rep.get('idea_sparks', []))
        if not ideas:
            fails.append('report has no ideas (and no research_opportunities/idea_sparks)')
            return ideas, fails
        fails.append('LEGACY: report uses research_opportunities/idea_sparks instead of single `ideas` list (please merge)')

    n = len(ideas)
    if n == 0:
        fails.append('report has 0 ideas')
        return ideas, fails

    cform = Counter(i.get('idea',{}).get('contribution_form') for i in ideas)
    mtype = Counter(i.get('idea',{}).get('method_type') for i in ideas)
    strat = Counter(i.get('strategy') for i in ideas)

    # Strategy coverage
    has_ecosystem = strat.get('ecosystem_distortion', 0) >= 1
    has_phenomenon_or_hidden = (strat.get('phenomenon_discovery', 0) +
                                 strat.get('hidden_failure_mode', 0)) >= 1
    if not has_ecosystem:
        fails.append('REPORT: no ecosystem_distortion (need ≥ 1)')
    if not has_phenomenon_or_hidden:
        fails.append('REPORT: no phenomenon_discovery or hidden_failure_mode (need ≥ 1)')

    # Domain relevance ≥ 70%. Legacy reports can still use is_se_related as fallback.
    domain_count = sum(
        1 for i in ideas
        if i.get('is_domain_relevant') or i.get('is_se_related') or i.get('domain_tags')
    )
    if domain_count / n < 0.70:
        fails.append(
            f'REPORT: domain-relevant {domain_count}/{n} = {100*domain_count/n:.0f}% < 70%'
        )

    # C1: better_solution ≤ 30%
    bs_pct = cform.get('better_solution', 0) / n
    if bs_pct > 0.30:
        fails.append(f'C1 VIOLATED: better_solution {cform.get("better_solution",0)}/{n} = {100*bs_pct:.0f}% > 30%')

    # C2: better_solution × preprint_risk=high ≤ 1
    high_bs = sum(1 for i in ideas
                  if i.get('idea',{}).get('contribution_form')=='better_solution'
                  and i.get('stress_test',{}).get('preprint_risk')=='high')
    if high_bs > 1:
        fails.append(f'C2 VIOLATED: better_solution × preprint_risk=high = {high_bs} (max 1)')

    # C3: new_problem ≥ 40%
    np_pct = cform.get('new_problem', 0) / n
    if np_pct < 0.40:
        fails.append(f'C3 VIOLATED: new_problem {cform.get("new_problem",0)}/{n} = {100*np_pct:.0f}% < 40%')

    # 旧约束: technical × better_solution ≤ 20%
    tb = sum(1 for i in ideas
             if i.get('idea',{}).get('method_type')=='technical_contribution'
             and i.get('idea',{}).get('contribution_form')=='better_solution')
    if tb / n > 0.20:
        fails.append(f'OLD CONSTRAINT VIOLATED: technical × better_solution = {tb}/{n} > 20%')

    return ideas, fails


def main():
    paths = []
    for arg in sys.argv[1:]:
        paths.extend(glob.glob(arg) if '*' in arg else [arg])
    if not paths:
        print('Usage: validate_idea_report.py <report.json>', file=sys.stderr)
        sys.exit(2)

    overall_fail = False

    for p in paths:
        path = Path(p)
        print(f'\n=== {path.name} ===')
        try:
            rep = json.loads(path.read_text())
        except Exception as e:
            print(f'  ✗ FAILED TO LOAD: {e}')
            overall_fail = True
            continue

        ideas, report_fails = check_report(rep)
        all_idea_fails = []
        for i, it in enumerate(ideas):
            all_idea_fails.extend(check_idea(it, f'idea#{i+1}'))

        if not report_fails and not all_idea_fails:
            n = len(ideas)
            cform = Counter(i.get('idea',{}).get('contribution_form') for i in ideas)
            print(f'  ✅ ALL CONSTRAINTS PASS ({n} ideas: '
                  f'{cform.get("new_problem",0)} new_problem, '
                  f'{cform.get("new_solution",0)} new_solution, '
                  f'{cform.get("better_solution",0)} better_solution)')
        else:
            for f in report_fails:
                print(f'  ✗ {f}')
            for f in all_idea_fails:
                print(f'  ✗ {f}')
            overall_fail = True
            print(f'\n  Total: {len(report_fails)} report-level + {len(all_idea_fails)} idea-level violations')

    sys.exit(1 if overall_fail else 0)


if __name__ == '__main__':
    main()
