---
name: daily-paper-analysis
description: 分析当日爬取的论文，生成 daily 研究报告（idea + 主题 + 顶级论文 + 研究机会）。包含 idea 生成的方法论流程（idea/motivation/novelty/feasibility/evaluation + FINER + stress_test + AI 失败模式自检）。触发：「生成 daily report」「分析今日论文」「生成研究报告」「找今日 idea」
---

# Daily Paper Analysis Skill

## 任务

读今日（或指定日期）爬取的论文，生成 daily report JSON 保存到 `output/reports/report_YYYYMMDD_HHMM.json`。重点：论文梳理 + 探索可能的研究 topic 与 idea。

## 必须先确认（CLAUDE.md 协议）

在动手前用下面模板输出，等用户确认：

```
准备执行 Daily Paper Analysis，将使用：

📄 Default：
  - prompts/commands/daily_report.md（slash 入口 + JSON schema）
  - prompts/methodology/idea-generation-method.md（idea 生成方法论）

🛠 Skills 可选启用：
  □ se-pattern-discovery     （扫信号 / 找反常时用 7-cut EDA）
  □ se-idea-framing          （把 idea 升级到顶会 framing 时用）
  □ se-idea-evaluation       （第二轮 idea 复评）

📋 流程：
  1. 加载今日 papers + 筛选
  2. 信号扫描（按 idea-method §0.5 中 5 类信号）
  3. 主题归纳 (themes) + 顶级论文 (top_papers) + se_spotlight
  4. 生成 idea_sparks / research_opportunities（按 idea-method 5 大字段）
  5. 校验（FINER avg ≥ 3.0 / 反 pattern 全过 / one_liner 单句 plain）
  6. 保存 JSON 到 output/reports/

✅ 确认开始？或要调整？
```

## 默认依赖文件（路径写绝对，确保正确）

**必读**：
- `prompts/commands/daily_report.md` — 报告大纲 / 步骤 / 输出 JSON schema
- `prompts/methodology/idea-generation-method.md` — idea 五大字段 + FINER + stress_test + ai_failure_mode_check + Concession Threshold

**今日论文数据**：
- `output/papers/papers_YYYYMMDD_*.json` — 当日爬虫输出（若无 → 提示用户先跑 paper_scraper.py）

## 可选 skills（按需启用）

| Skill | 何时启用 |
|---|---|
| `se-pattern-discovery` | 扫信号阶段想做 7-cut EDA 找反常 |
| `se-literature-search` | **(强制)** 任何 new_problem idea 在 commit 前真去 arxiv/OpenAlex search 确认无 prior |
| `se-citation-verification` | 生成后核查 closest_prior_work url 真实性 |
| `se-idea-framing` | 某条 idea 想升级到 ICSE/CCS 级 framing 时 |
| `se-idea-evaluation` | 想用 FINER 之外的 5d 评分体系做二次校验 |
| `se-reviewer-psychology` | 写 stress_test.strongest_counter 时想更精准模拟 reviewer |
| `se-narrative-engineering` | 想给 executive_summary 加强 narrative 时 |

## 流程详解

### Step 0 — 加载 feedback log（强制）

**必须 Read** `prompts/methodology/idea_feedback_log.md` §2 blacklist。把它当作 candidate idea 必过的 hard filter。

### Step 0.5 — Full-text 阅读顶 paper（强制）

筛 top 5 信号 paper 后，**WebFetch 完整 PDF**，抽取每篇：
- Limitations 节
- Discussion / Future Work
- Threats to Validity

这些是 idea 真 anchor。仅靠 abstract 推 idea = N+1 增量。

### Step 1 — 加载论文
```bash
ls -t output/papers/papers_*.json | head -1
```
Read 该文件全量，统计：总篇 / 有 abstract / 来源分布。

### Step 2 — 筛选
- 优先 cs.DB 全保留（最多 56）
- 其他来源各源 round-robin 选有 abstract 的
- 排除 "Proceedings of *" 类目录页
- 上限 120 篇

### Step 3 — 信号扫描（关键）
按 `idea-generation-method.md §0.5` 的 5 类信号扫：
- 失真信号 / 测量空白 / 承重假设 / 新 affordance / surprise

每条信号 → 引用具体论文 + 1 句反常描述。

### Step 4 — 生成 themes / top_papers / db_spotlight
- themes: 6-8 个，标 `hot|rising|stable`
- top_papers: 8-10 篇最值得关注的
- db_spotlight: DB/分布式/Web3 专项子领域深化（数据库引擎/共识协议/智能合约/DeFi 安全等）

### Step 5 — 生成 ideas（单 ideas 列表，按 5 大字段 schema）

**🚨 Prior-Art 真实搜索硬约束（任何 new_problem 标签前必做）**：
对每个想标为 `contribution_form = new_problem` / `novelty_type = unsolved_problem` 的 idea，**生成前必须**：
1. 用 `se-literature-search` skill 搜：title 主词 + 同义词组（OpenAlex + arxiv 两源）
2. 检查近 6 个月 preprint，如有直接 prior：标 `preprint_risk=high` + closest_prior_work 必写 differentiation + preprint_risk_reason 含 reframe 路径——**不自动降级，不 cut**，保留 idea 给用户决策
3. 完整搜索后即可 commit 该 idea（contribution_form 由作者意图决定，不由 prior 撞决定）

**事故案例**（2026-05-23）：「CI/CD Agentic Workflow Injection」标 new_problem，但 Wang et al. arXiv 2605.07135 直接覆盖。**未做真实 search = 必撞车**。当时是 cut，现策略：保留 + 标 high risk + 列 prior。

**5 大字段 schema**：
- idea（formulation_type + one_liner + approach）
- motivation（why_matters + signal）
- novelty（novelty_type + statement + closest_prior_work + delta）
- feasibility（level + data + effort + risks）
- evaluation（expected_findings + null_result）
- finer + stress_test + ai_failure_mode_check

**硬约束**：
- `one_liner` ≤ 30 字、单句、plain、禁 jargon
- core_claim 严禁数值（数值全在 evaluation）
- FINER avg ≥ 3.0 且无单项 < 2
- 至少 1 个 ecosystem_distortion + 至少 1 个 phenomenon_discovery / hidden_failure_mode
- better_solution ≤ 30%
- 至少 50% SE 相关

### Step 6 — 保存
```
output/reports/report_YYYYMMDD_HHMM.json
```

## 输出后必做

1. JSON 校验：`python3 -c "import json,sys; json.load(open('<path>'))"`
2. 完整校验：`python3 scripts/validate_idea_report.py <path>`（11 类硬约束）
3. 浏览器提示：http://127.0.0.1:7860 「研究报告」标签

## 用户反馈处理（强制）

用户 review 报告后，若任何 idea 被拒：
1. 记录 rejection reason + prior 论文（如有）
2. **Prepend** 到 `prompts/methodology/idea_feedback_log.md` §3
3. 若发现新 pattern → 加到 §2 blacklist
4. 这是「不再犯」机制，比 silent fix 高 leverage

## 用户响应

- 「确认 / 开始 / 好」→ 执行 6 步
- 「启用 N」→ 启用某可选 skill，重新确认
- 「跳过 N」→ 跳过某步骤
- 「换 X 为 Y」→ 替换默认方法论后重新确认
