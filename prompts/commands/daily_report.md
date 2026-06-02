# 每日论文调研报告生成任务

## 你的任务

执行以下步骤，生成今日论文调研报告并保存到文件，供网页展示。本项目只聚焦：

- 数据库 / 数据系统
- 分布式系统 / 网络系统
- Web3 / 区块链 / DeFi / 智能合约安全

任何需要 LLM 分析的环节都按 Prompt-as-Program 执行：自己读取论文与 prompt 后完成分析，不调用外部 LLM API。

---

## 步骤 1：加载论文数据

用 Bash 工具找到最新的论文文件：

```bash
ls -t output/papers/papers_*.json | head -1
```

然后读取该文件的完整内容。若不存在，提示用户先运行：

```bash
python paper_scraper.py --max 50
```

---

## 步骤 2：筛选论文

从所有论文中：

- 优先选取有 `abstract` 字段且非空的论文
- 排除标题以 `"Proceedings of"` 开头的目录页
- 最多选取前 120 篇（按原始顺序）
- 记录：总论文数、筛选后论文数、来源分布（arxiv / paperscool / db:* / dist:* / net:* / sec:* / web3:*）

**领域优先规则**：

- 默认优先保留 `cs.DB / cs.DC / cs.NI / cs.CR / cs.PL` 与顶会来源论文。
- `cs.SE` 只作为 `paper_scraper.py --include-se` 的可选交叉来源，不再作为默认优先领域。
- 若需要截断，按 `database / distributed_systems / web3 / network / programming_languages` 五类 round-robin，避免单一来源淹没其他领域。

---

## 步骤 3：深度分析

仔细阅读每篇论文的标题、摘要和来源，完成以下分析。

### 3a. 通用主题分析（6-8 个）

识别当前研究热点主题，为每个主题标注：

- `trend`：`hot`（3 篇以上）/ `rising`（有新进展）/ `stable`（持续研究）
- 代表性论文序号（最多 5 篇）
- 关键词（3 个）

### 3b. 领域专题分析（必须包含）

专门分析 DB / 分布式 / Web3 相关论文，至少覆盖有论文命中的领域：

- **数据库与数据系统**：查询优化、事务、索引、存储引擎、HTAP、流处理、数据湖仓、向量数据库
- **分布式系统与网络**：一致性、共识、复制、容错、云原生、服务网格、边缘计算、网络测量
- **Web3 / 区块链 / DeFi**：智能合约安全、MEV、预言机、跨链、rollup、账户抽象、链上治理
- **安全与密码经济学交叉**：S&P / CCS / FC 中与 Web3、DeFi、零知识、去中心化系统有关的论文
- **PL / 智能合约语言交叉**：Solidity/EVM 分析、合约验证、程序语言机制对 Web3 安全的影响

如果某一主领域论文数量少于 3 篇，也要单独说明「今天信号弱」还是「爬取源覆盖不足」。

### 3c. 顶级论文（8-10 篇）

从所有论文中挑选最值得关注的，给出简洁推荐理由（35 字以内）。优先选择：

- 顶会论文
- 有清晰系统/数据/安全问题定义的论文
- 对 DB / 分布式 / Web3 研究 agenda 有启发的论文

### 3d. Ideas（6-10 个，单列表）

**强制**：严格按 `prompts/methodology/idea-generation-method.md` 完整框架生成。
**已合并 opps + sparks**：只产出单一 `ideas` 列表。

**三个强制前置**：

1. 读取 `prompts/methodology/idea_feedback_log.md` §2 blacklist，所有 candidate idea 比对。
2. Full-text 阅读 top 5 信号 paper（WebFetch 完整 PDF 或开放 HTML），抽 Limitations / Discussion / Future Work。
3. 每个 `new_problem` idea 做真实 prior-art search：至少 arxiv + OpenAlex / Semantic Scholar / WebSearch 中两类来源。

**Idea 阶段必填（违反整条丢弃）**：

- `starting_point / idea / motivation / novelty / feasibility / evaluation` 全部填齐
- `idea.formulation_type / method_type / contribution_form` 三个枚举字段全选
- `idea.one_liner` ≤ 30 字单句 plain Chinese；严禁数值与空泛 jargon
- `strategy` ∈ 6 类；`novelty.novelty_type` ∈ 3 类
- `domain_tags` 至少 1 个，取值见 JSON schema
- `novelty.closest_prior_work` ≥ 1 项（每项 `what_they_did + what_we_dont_do` 都具体）
- `better_solution` 类 L 与 I 均有数值（在 `evaluation.expected_findings` 中）
- `feasibility.key_risks` 是执行风险（不要写「实验失败」）
- `evaluation.expected_findings` 是量化预测；`null_result` 是可观测信号
- `finer` 平均 ≥ 3.0 且无单项 < 2
- `stress_test` 含 `preprint_risk`；high 必须在 `preprint_risk_reason` 写 reframe 路径
- `ai_failure_mode_check.frame_lock` 必填

**Report-level（违反整篇丢弃）**：

- 至少 1 个 `ecosystem_distortion`
- 至少 1 个 `phenomenon_discovery / hidden_failure_mode`
- 至少 70% ideas 为 `is_domain_relevant=true`
- 如果输入数据允许，`domain_tags` 至少覆盖 2 个主领域
- **C1**: `better_solution` 总占比 ≤ 30%
- **C2**: `better_solution × preprint_risk=high` ≤ 1
- **C3**: `new_problem` 总占比 ≥ 40%
- `technical × better_solution` ≤ 20%

**Concession Threshold**（用户 pushback 时）：按 `idea-generation-method.md §7` 打分；不到 4 不让步。

**保存后自动校验**：

```bash
python3 scripts/validate_idea_report.py output/reports/report_*.json
```

---

## 步骤 4：生成报告 JSON

将分析结果组织为以下严格 JSON 结构（所有文字用中文）：

```json
{
  "generated_at": "YYYY-MM-DD HH:MM",
  "source_file": "papers_YYYYMMDD_HHMM.json",
  "total_papers": 0,
  "analyzed_papers": 0,
  "source_distribution": {"arxiv:cs.DB": 0, "db:vldb2026": 0},
  "executive_summary": "200字以内：今日 DB/Web3/分布式研究全景、核心趋势、值得关注的信号",
  "themes": [
    {
      "name": "主题名（中文，6字以内）",
      "trend": "hot|rising|stable",
      "count_estimate": 0,
      "description": "60字：这个主题在研究什么、为何重要",
      "keywords": ["词1", "词2", "词3"],
      "papers": [
        {"title": "...", "url": "...", "source": "...", "published": "..."}
      ]
    }
  ],
  "domain_spotlight": {
    "summary": "100字：今日 DB/Web3/分布式领域概览",
    "subtopics": [
      {
        "name": "子领域名（如：共识协议）",
        "domain": "database|distributed_systems|web3|network|security|programming_languages",
        "paper_count": 0,
        "highlights": "50字：该子领域的主要发现或进展",
        "papers": [
          {"title": "...", "url": "...", "source": "...", "published": "..."}
        ]
      }
    ]
  },
  "top_papers": [
    {
      "title": "...",
      "url": "...",
      "source": "...",
      "published": "...",
      "reason": "35字：为何值得重点关注"
    }
  ],
  "ideas": [
    {
      "title": "≤15字",
      "strategy": "phenomenon_discovery|assumption_break|ecosystem_distortion|hidden_failure_mode|new_problem_class|better_solution",
      "is_domain_relevant": true,
      "domain_tags": ["database|distributed_systems|web3|network|security|programming_languages"],
      "starting_point": {
        "sp_rating": "SP_solid|SP_weak|SP_invalid",
        "source_type": "main_finding|secondary_finding|limitation|footnote|user_observation",
        "operationalizability": "≤60字：如何定义和测量",
        "author_stance": "pursuing|neutral|abandoned",
        "sp_invalid_reason": "仅 SP_invalid 填"
      },
      "idea": {
        "formulation_type": "hypothesis|research_question|proposed_construct",
        "method_type": "empirical_study|technical_contribution|theoretical|vision_position",
        "contribution_form": "new_problem|new_solution|better_solution",
        "one_liner": "≤30字 单句 plain Chinese 禁 jargon 非专家秒懂",
        "approach": "≤120字"
      },
      "motivation": {
        "why_matters": "≤80字",
        "signal": {
          "summary": "≤40字 trigger",
          "source_papers": [{"title": "...", "url": "...", "source": "..."}]
        }
      },
      "novelty": {
        "novelty_type": "unsolved_problem|research_gap|better_solution",
        "statement": "≤80字",
        "closest_prior_work": [
          {"title": "...", "url": "...", "what_they_did": "≤60字", "what_we_dont_do": "≤60字"}
        ],
        "delta_over_prior": "≤80字",
        "search_evidence": [{"query": "...", "summary": "≤80字", "sources": ["arxiv", "OpenAlex"]}]
      },
      "feasibility": {
        "feasibility_level": "high|medium|low",
        "data_source": "≤60字",
        "effort_estimate": "1人月|3人月|6人月+|12人月+",
        "key_risks": ["≤30字 执行风险", "≤30字 执行风险"]
      },
      "evaluation": {
        "expected_findings": "≤100字 量化预测",
        "null_result": "≤60字 可观测信号"
      },
      "finer": {"feasible": 1, "interesting": 1, "novel": 1, "ethical": 1, "relevant": 1, "average": "X.X"},
      "stress_test": {
        "strongest_counter": "≤80字",
        "biggest_confound": "≤80字 推理风险",
        "fallacy_risk": "confirmation_bias|hasty_generalization|cherry_picking|survivorship_bias|ecological_fallacy|none",
        "preprint_risk": "high|medium|low",
        "preprint_risk_reason": "≤80字"
      },
      "ai_failure_mode_check": {
        "frame_lock": "≤60字（≥1 alternative framing 必）",
        "bug_as_insight": "≤60字或 N/A",
        "shortcut_risk": "≤60字或 N/A"
      },
      "papers": [{"title": "...", "url": "...", "source": "...", "published": "..."}]
    }
  ]
}
```

---

## 步骤 5：保存报告文件

用 Bash 工具获取当前时间戳，然后将完整 JSON 保存到：

```text
output/reports/report_YYYYMMDD_HHMM.json
```

时间戳格式示例：`report_20260602_1430.json`。

---

## 步骤 6：确认

完成后输出：

```text
报告已保存：output/reports/report_YYYYMMDD_HHMM.json
共分析 N 篇论文（M 条 idea 为领域相关）
刷新浏览器「研究报告」标签查看：http://127.0.0.1:7860
```

---

## 注意事项

- 全部输出内容使用中文
- JSON 中不要有注释，不要有 markdown 代码块包裹
- 如果论文数量充足，themes 至少 6 个，并覆盖 DB / 分布式 / Web3 中至少 2 个主领域
- `domain_spotlight` 是对 `themes` 中领域内容的补充深化，两者可以重叠
- 确保 JSON 格式合法（可用 `python3 -m json.tool <file>` 验证）
- `ideas` 单列表必须严格按 `prompts/methodology/idea-generation-method.md` 的 schema 输出
