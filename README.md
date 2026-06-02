# 数据库 / Web3 / 分布式系统 论文追踪与研究报告系统

自动爬取 **数据库（Database）、Web3/区块链、分布式系统** 领域的顶级学术论文，通过 Web 界面浏览，并由 Claude Code 生成深度研究报告与 idea。

## 领域覆盖

| 方向 | 顶会 | arxiv |
|---|---|---|
| 数据库 | VLDB / SIGMOD / ICDE | cs.DB |
| 分布式系统 | OSDI / SOSP / NSDI / USENIX ATC / EuroSys | cs.DC |
| 网络 | SIGCOMM | cs.NI |
| Web3 安全 | IEEE S&P / ACM CCS / Financial Cryptography | cs.CR |
| 智能合约 / PL | — | cs.PL |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 爬取今日论文

```bash
python paper_scraper.py --max 50
```

### 3. 启动 Web 界面

```bash
python web_app.py
# 访问 http://127.0.0.1:7860
```

### 4. 生成研究报告

**推荐方式 — 一键全流程**（在 Claude Code 里）：

```
/full-cycle              ← 当日例行（爬虫 + daily 分析 + idea 评估 + digest）
/full-cycle weekly       ← 周复盘（含 7 天 cross-paper 分析）
/full-cycle monthly      ← 月复盘
/full-cycle conf:vldb2025 ← VLDB 会议综述
```

---

## 命令使用指南

### 我想做什么 → 用什么命令

| 场景 | 命令 |
|---|---|
| 当天爬到的论文都跑一遍 | `/full-cycle` |
| 过去一周论文趋势 | `/full-cycle weekly` |
| 某个会议全部论文综述 | `/full-cycle conf:sigmod2025` |
| 调研某个主题的研究现状 | `/full-cycle topic:<主题>` |
| 只调研主题，不重新爬 | `/topic-report <主题>` |
| 只爬论文 | `python paper_scraper.py --max 50` |

### 主题专项示例

```
/topic-report distributed transaction
/topic-report blockchain smart contract security
/topic-report DeFi MEV attack
/topic-report query optimization learned index
/topic-report consensus fault tolerance Byzantine
/topic-report zero-knowledge proof blockchain
/topic-report distributed database HTAP
```

---

## 论文来源

| 来源 | 说明 |
|------|------|
| arxiv | 默认 cs.DB / cs.DC / cs.NI / cs.CR / cs.PL；`--include-se` 时额外纳入 cs.SE |
| papers.cool | 同 arxiv 分类，当日热门 |
| VLDB | 数据库顶会（via DBLP）|
| SIGMOD | 数据库顶会（via DBLP）|
| ICDE | 数据库顶会（via DBLP）|
| OSDI | 操作系统与分布式系统（via DBLP + USENIX 摘要）|
| SOSP | 系统顶会（via DBLP）|
| NSDI | 网络与分布式（via DBLP + USENIX 摘要）|
| SIGCOMM | 网络系统顶会（via DBLP）|
| USENIX ATC | 系统年度技术会议（via DBLP + USENIX 摘要）|
| EuroSys | 欧洲系统顶会（via DBLP）|
| IEEE S&P | 安全顶会（Web3/区块链安全）（via DBLP）|
| ACM CCS | 安全顶会（智能合约/密码学）（via DBLP）|
| Financial Cryptography | 密码经济学/DeFi（via DBLP）|

---

## paper_scraper.py 参数

```
--max N          每个来源最多抓取 N 篇（默认 20）
--proxy URL      HTTP 代理，如 http://127.0.0.1:7890
--claude-key KEY Claude API Key（生成中文摘要）
--domain-only    只保留 DB/分布式/Web3 相关论文（内置关键词）
--keywords K,..  自定义过滤关键词，逗号分隔
--no-arxiv       跳过 arxiv
--no-paperscool  跳过 papers.cool
--no-confs       跳过所有顶会（VLDB/SIGMOD/OSDI 等）
--force-confs    强制重新爬取已爬过的会议
--include-se     额外纳入 cs.SE（仅用于智能合约工程实践等交叉主题）
```

常用示例：

```bash
# 只爬 arxiv + papers.cool（快速，无顶会）
python paper_scraper.py --max 50 --no-confs

# 只保留 DB/分布式/Web3 相关论文
python paper_scraper.py --max 50 --domain-only

# 自定义关键词过滤
python paper_scraper.py --max 50 --keywords "blockchain,smart contract,consensus"

# 每日定时任务
bash run_daily.sh
```

---

## 一键全流程 `/full-cycle`

| 参数 | 含 Step | 适用场景 |
|---|---|---|
| `daily`（缺省）| 1 + 2 + 4 + 5 | 当日例行 |
| `weekly` | 1 + 2 + 3 (7d) + 4 + 5 | 周复盘 |
| `monthly` | 1 + 2 + 3 (30d) + 4 + 5 | 月复盘 |
| `conf:<name>` | 1 + 2 + 3 (全集) + 4 + 5 | 会议综述 |
| `topic:<X>` | 1 + 2T + 4 + 5 | 主题专项 |

---

## 目录结构

```
.
├── paper_scraper.py      # 爬虫主程序（DB/分布式/Web3 领域）
├── web_app.py            # Flask Web 服务（:7860）
├── run_daily.sh          # 每日定时爬取脚本
├── requirements.txt
├── scripts/
│   └── validate_idea_report.py
├── templates/
│   └── index.html
├── prompts/              # Claude Code 执行 prompt
└── output/
    ├── papers/           # papers_*.json / *.md
    ├── reports/          # report_*.json + eval_*.json
    ├── pilots/           # pilot 实验结果
    └── sessions/         # JSONL transcripts
```

---

## 依赖

- Python 3.9+
- `requests` + `beautifulsoup4`：爬虫
- `flask` + `flask-socketio`：Web 服务
- `anthropic`（可选）：生成中文摘要
