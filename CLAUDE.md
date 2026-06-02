# Reading Paper DB — 项目规范

## 领域定位

本项目专注于 **数据库（Database）、Web3/区块链（Blockchain/DeFi）、分布式系统（Distributed Systems）** 三大领域的学术论文追踪与研究 idea 生成。

覆盖会议：VLDB / SIGMOD / ICDE（数据库）、OSDI / SOSP / NSDI / USENIX ATC / EuroSys（分布式系统）、IEEE S&P / ACM CCS / Financial Cryptography（Web3 安全）

arxiv 分类：cs.DB / cs.DC / cs.NI / cs.CR / cs.PL / cs.SE

---

## 4 阶段工作流

```
Step 1  paper_scraper.py        ← 爬论文（arxiv daily / 会议 annual + 去重）
   ↓
Step 2  daily-paper-analysis    ← 分析当日论文 → 生成 daily report + idea
   ↓
Step 3  lookback-cross-analysis ← 跨时段（7d/30d/会议）做 cross-paper 分析
   ↓
Step 4  idea-evaluation         ← 任何阶段对 idea 做严格质量评估（FINER+stress+failure）
   ↓
Step 4.5  pilot-experiment      ← 对通过 eval 的 idea 做最小可行实验（20-50 样本），验证核心假设可行性（Go/Yellow/Red）
   ↓
Step 5  digest_template         ← 把 1-5 产出拼成人类可读 markdown digest
```

**除 Step 1（爬虫）外，其余全部 skill 化**，见 `.claude/skills/`。

### 一键全流程：`/full-cycle [daily|weekly|monthly|conf:X]`

| 命令 | 含 Step | 用途 |
|---|---|---|
| `/full-cycle` (= daily) | 1+2+4+5 | 当日例行 |
| `/full-cycle weekly` | 1+2+3(7d)+4+5 | 周复盘 |
| `/full-cycle monthly` | 1+2+3(30d)+4+5 | 月复盘 |
| `/full-cycle conf:vldb2025` | 1+2+3(全集)+4+5 | 会议综述 |
| `/full-cycle topic:<X>` | 1+2T+4+5 | 主题专项（Step 2T = /topic-report 替 daily）|

### 主题专项：`/topic-report <topic>`

```
/topic-report distributed transaction
/topic-report blockchain smart contract security
/topic-report query optimization LLM
/topic-report DeFi MEV attack
/topic-report consensus protocol fault tolerance
```

输出文件：`output/reports/report_<topic-slug>_<ts>.json`

**关键例外**：`/full-cycle` 跑时，子 skill 的「必须先确认」段被 **Step 0 一次性确认** 覆盖，不再逐 skill 二次确认；其余质量门（§2 blacklist / WebSearch prior / validator C1/C2/C3 / FINER）**全保留**。失败必停，不静默 retry。

---

## 核心行为准则

### Prompt-as-Program（始终生效）

**任何需要 LLM 分析的任务，Claude 自己作为执行引擎完成，不调用外部 LLM API。**

具体规则见 `.claude/commands/prompt-as-program.md`。

触发场景：「生成报告」「总结这些论文」「分析趋势」「找研究空白」。

执行前先在 `prompts/` 写好可复用 prompt 文件，然后按它执行。

### Skill/Prompt 使用确认协议（始终生效）

**每次接到「分析论文」「写报告」「生成 idea」「找研究空白」「评估 idea」类任务时，开始执行前必须先确认将用哪些 skill / prompt 文件。**

确认格式：
```
准备执行 [任务名]，将使用：

📄 Prompt 文件：
  - prompts/methodology/<file>.md （作用）
  - prompts/commands/<file>.md （作用）

🛠 Skills：
  - <skill-name> （作用，default / 可选）

📋 流程概要：
  Step 1 → Step 2 → ...

✅ 确认开始？或要调整？
```

用户响应：「确认 / 开始 / 好」→ 执行；「改 X / 跳过 Y / 换 Z」→ 调整后再确认；「不用 X」→ 移除。

**例外**：
- 纯查询任务（解释字段、问 FINER 几分等只读问题）不需要确认。
- `/full-cycle` 一键流水线下，**单次** Step 0 确认覆盖全部子 skill。

---

## 目录结构

```
reading-paper-db/
├── .claude/
│   ├── commands/                    ← Slash command shortcuts
│   │   ├── full-cycle.md
│   │   ├── topic-report.md
│   │   └── prompt-as-program.md
│   └── skills/                      ← 项目 skills
│       ├── daily-paper-analysis/SKILL.md      ← Step 2
│       ├── lookback-cross-analysis/SKILL.md   ← Step 3
│       ├── idea-evaluation/SKILL.md           ← Step 4
│       └── pilot-experiment/SKILL.md          ← Step 4.5
│
├── prompts/                         ← 项目 prompts
│   ├── README.md
│   ├── methodology/
│   │   ├── idea-generation-method.md
│   │   ├── idea_feedback_log.md
│   │   └── digest_template.md
│   └── commands/
│       ├── daily_report.md
│       └── prompt-as-program.md
│
├── output/
│   ├── papers/                      ← 爬虫输出 papers_*.json/.md
│   ├── reports/                     ← report_*.json + eval_*.json
│   ├── pilots/                      ← pilot_*.json
│   └── sessions/                    ← session JSONL transcripts
│
├── scripts/
│   └── validate_idea_report.py
├── templates/
│   └── index.html
├── paper_scraper.py                 ← Step 1
├── web_app.py                       ← Flask UI :7860
└── run_daily.sh
```

## 主要脚本

| 脚本 | 作用 |
|------|------|
| `paper_scraper.py` | 爬论文（arxiv cs.DB/cs.DC/cs.NI/cs.CR/cs.PL + DB/分布式/Web3 顶会） |
| `web_app.py` | Flask Web UI（:7860） |

## 论文来源

| 来源 | 说明 |
|---|---|
| arxiv | cs.DB / cs.DC / cs.NI / cs.CR / cs.PL / cs.SE |
| papers.cool | cs.DB / cs.DC / cs.NI / cs.CR（当日热门） |
| VLDB / SIGMOD / ICDE | 数据库顶会（via DBLP） |
| OSDI / SOSP / NSDI / ATC / EuroSys | 分布式系统顶会（via DBLP） |
| IEEE S&P / ACM CCS | Web3 安全顶会（via DBLP） |
| Financial Cryptography | 密码经济学/Web3（via DBLP） |

## paper_scraper.py 参数

```
--max N          每个来源最多抓取 N 篇（默认 20）
--proxy URL      HTTP 代理
--claude-key KEY Claude API Key（生成中文摘要）
--domain-only    只保留 DB/分布式/Web3 相关论文
--keywords K,..  自定义过滤关键词
--no-arxiv       跳过 arxiv
--no-paperscool  跳过 papers.cool
--no-confs       跳过顶会（VLDB/SIGMOD/OSDI 等）
--force-confs    强制重新爬取已爬过的会议
```

## 安装的全局 se-* skills

- `se-idea-framing` / `se-idea-generation` / `se-idea-evaluation`
- `se-pattern-discovery` / `se-abductive-iteration` / `se-exploratory-first`
- `se-reviewer-psychology` / `se-narrative-engineering`
- `se-literature-search` / `se-literature-synthesis` / `se-citation-verification`

**4 个项目 skills**（仅本项目可见）：
- `daily-paper-analysis` / `lookback-cross-analysis` / `idea-evaluation` / `pilot-experiment`
