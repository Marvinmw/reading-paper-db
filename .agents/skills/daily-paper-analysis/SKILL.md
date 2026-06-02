---
name: daily-paper-analysis
description: 分析当日爬取的 DB/Web3/分布式系统论文，生成 daily 研究报告（主题 + 顶级论文 + ideas）。包含 idea 生成方法论流程（starting_point + idea/motivation/novelty/feasibility/evaluation + FINER + stress_test + AI 失败模式自检）。触发：「生成 daily report」「分析今日论文」「生成研究报告」「找今日 idea」
---

# Daily Paper Analysis Skill

## 任务

读取今日（或指定日期）爬取的论文，生成 daily report JSON 保存到 `output/reports/report_YYYYMMDD_HHMM.json`。重点：DB / Web3 / 分布式系统论文梳理 + 可评估研究 idea。

## 必须先确认（AGENTS.md 协议）

在动手前用下面模板输出，等用户确认：

```text
准备执行 Daily Paper Analysis，将使用：

📄 Prompt 文件：
  - prompts/commands/daily_report.md（daily 入口 + JSON schema）
  - prompts/methodology/idea-generation-method.md（idea 生成方法论）
  - prompts/methodology/idea_feedback_log.md（blacklist + rejection history）
  - prompts/commands/prompt-as-program.md（不调用外部 LLM API）

🛠 Skills：
  - daily-paper-analysis（当前任务）
  - idea-evaluation（可选：对生成 idea 做二次质量门）
  - pilot-experiment（可选：对通过 eval 的 idea 做最小验证）

📋 流程概要：
  Step 1 加载最新 papers
  Step 2 领域筛选与来源统计
  Step 3 主题归纳 + domain_spotlight + top_papers
  Step 4 生成 ideas（含 prior-art search evidence）
  Step 5 validate_idea_report.py 校验
  Step 6 保存到 output/reports/

✅ 确认开始？或要调整？
```

## 默认依赖文件

**必读**：

- `prompts/commands/daily_report.md` — 报告大纲 / 步骤 / 输出 JSON schema
- `prompts/methodology/idea-generation-method.md` — idea schema + FINER + stress_test + Concession Threshold
- `prompts/methodology/idea_feedback_log.md` — §2 blacklist
- `prompts/commands/prompt-as-program.md` — 不调用外部 LLM API

**今日论文数据**：

- `output/papers/papers_YYYYMMDD_*.json` — 当日爬虫输出
- 若无文件，提示用户先运行 `python paper_scraper.py --max 50`

## 流程详解

### Step 0 — 加载 feedback log（强制）

读取 `prompts/methodology/idea_feedback_log.md` §2 blacklist。把它当作 candidate idea 的 risk filter；命中后必须提高 preprint_risk 并写清 differentiation。

### Step 0.5 — Full-text 阅读顶 paper（强制）

筛 top 5 信号 paper 后，尽量 WebFetch 完整 PDF / HTML，抽取：

- Limitations
- Discussion / Future Work
- Threats to Validity / Caveats

这些是 idea anchor。仅靠 abstract 推 idea 视为高 preprint risk。

### Step 1 — 加载论文

```bash
ls -t output/papers/papers_*.json | head -1
```

读取全量，统计：总篇数、有 abstract 篇数、来源分布。

### Step 2 — 领域筛选

- 默认领域：database / distributed_systems / web3 / network / security / programming_languages
- 优先保留 `cs.DB / cs.DC / cs.NI / cs.CR / cs.PL` 与 `db:* / dist:* / net:* / sec:* / web3:*`
- `cs.SE` 仅在爬虫使用 `--include-se` 时作为交叉来源，不作为默认优先领域
- 上限 120 篇；多来源 round-robin

### Step 3 — 信号扫描

按 `idea-generation-method.md §0.5` 的 5 类信号扫：

- 生态失真 / 测量空白 / 承重假设 / 新 affordance / surprise

每条信号引用具体论文 + 1 句反常描述。

### Step 4 — 生成 themes / top_papers / domain_spotlight

- `themes`: 6-8 个，标 `hot|rising|stable`
- `top_papers`: 8-10 篇最值得关注的
- `domain_spotlight`: DB/分布式/Web3/网络专项子领域深化（查询优化、共识协议、智能合约、DeFi 安全等）

### Step 5 — 生成 ideas（单 `ideas` 列表）

**Prior-Art 真实搜索硬约束**：

对每个 `contribution_form = new_problem` / `novelty_type = unsolved_problem` 的 idea，生成前必须：

1. 搜 title 主词 + 同义词组 + 关键技术词。
2. 至少覆盖 arxiv + OpenAlex / Semantic Scholar / WebSearch 中两类来源。
3. 检查近 6 个月 preprint；如有直接 prior，保留 idea 但标 `preprint_risk=high`，并写 `closest_prior_work` 与 reframe 路径。

**字段硬约束**：

- `starting_point`
- `is_domain_relevant`
- `domain_tags`
- `idea / motivation / novelty / feasibility / evaluation`
- `finer / stress_test / ai_failure_mode_check`

**报告硬约束**：

- 至少 1 个 `ecosystem_distortion`
- 至少 1 个 `phenomenon_discovery / hidden_failure_mode`
- 至少 70% ideas 为 `is_domain_relevant=true`
- `better_solution` ≤ 30%
- `new_problem` ≥ 40%

### Step 6 — 保存与校验

保存到：

```text
output/reports/report_YYYYMMDD_HHMM.json
```

随后执行：

```bash
python3 -m json.tool output/reports/report_YYYYMMDD_HHMM.json >/dev/null
python3 scripts/validate_idea_report.py output/reports/report_YYYYMMDD_HHMM.json
```

## 用户反馈处理（强制）

用户 review 报告后，若任何 idea 被拒：

1. 记录 rejection reason + prior 论文（如有）
2. Prepend 到 `prompts/methodology/idea_feedback_log.md` §3
3. 若发现新 pattern，更新 §2 blacklist

## 用户响应

- 「确认 / 开始 / 好」→ 执行
- 「启用 eval」→ 生成后调用 `idea-evaluation`
- 「跳过 full-text」→ 允许，但所有相关 idea 的 preprint_risk 至少 +1 档
