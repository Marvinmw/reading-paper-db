# 每日论文调研报告生成任务

## 你的任务

执行以下步骤，生成今日论文调研报告并保存到文件，供网页展示。

---

## 步骤 1：加载论文数据

用 Bash 工具找到最新的论文文件：

```bash
ls -t /Users/weima/Documents/crawer_paper/output/papers_*.json | head -1
```

然后用 Read 工具读取该文件的完整内容。

---

## 步骤 2：筛选论文

从所有论文中：
- 优先选取有 `abstract` 字段且非空的论文
- 排除标题以 "Proceedings of" 开头的目录页
- 最多选取前 120 篇（按原始顺序）
- 记录：总论文数、筛选后论文数、来源分布（arxiv/acl/openreview/paperscool）

**软件工程优先**：cs.SE 来源的论文无论是否有摘要都要优先纳入，最多保留全部 cs.SE 论文。

---

## 步骤 3：深度分析

仔细阅读每篇论文的标题、摘要和来源，完成以下分析：

### 3a. 通用主题分析（6-8 个）
识别当前研究热点主题，为每个主题标注：
- `trend`：`hot`（3篇以上）/ `rising`（有新进展）/ `stable`（持续研究）
- 代表性论文序号（最多5篇）
- 关键词（3个）

### 3b. 软件工程专项分析（必须包含）
专门分析与软件工程相关的论文，涵盖但不限于：
- **代码生成与补全**：LLM 用于代码生成、代码理解、代码翻译
- **程序分析与验证**：静态分析、符号执行、形式化验证、程序合成
- **软件测试**：自动化测试、测试生成、故障定位、Fuzzing
- **DevOps 与工程实践**：CI/CD、代码审查、技术债务、软件度量
- **安全与漏洞**：漏洞检测、代码安全、供应链安全
- **SE + LLM 交叉**：用 LLM 增强软件工程工具、Agent 辅助编程

如果论文数量少于 3 篇，也要单独列出，说明 SE 研究的现状与空白。

### 3c. 顶级论文（8-10 篇）
从所有论文中挑选最值得关注的，给出简洁的推荐理由（35字以内）。

### 3d. Ideas（6-10 个，单列表）

**强制**：严格按 `prompts/methodology/idea-generation-method.md` 完整框架生成。
**已合并 opps + sparks**——只产出单一 `ideas` 列表（不再分两段）。

**🚨 三个强制前置**：
1. Read `prompts/methodology/idea_feedback_log.md` §2 blacklist，所有 candidate idea 比对
2. Full-text 阅读 top 5 信号 paper（WebFetch 完整 PDF + 抽 Limitations/Discussion/Future Work）
3. 每个 new_problem idea 真实 web search arxiv prior

**Post-report**：用户拒 idea → prepend 到 idea_feedback_log.md §3 + 提炼到 §2 blacklist。

**Idea 阶段必填（违反整条丢弃）**：
- **5 大字段**：`idea / motivation / novelty / feasibility / evaluation` 全部填齐
- `idea.formulation_type / method_type / contribution_form` 三个枚举字段全选
- **`idea.one_liner` ≤ 30 字单句 plain Chinese**（最重要）；严禁数值与 jargon
- `strategy` ∈ 6 类；`novelty.novelty_type` ∈ 3 类
- `novelty.closest_prior_work` ≥ 1 项（每项 what_they_did + what_we_dont_do 都具体）
- `better_solution` 类 L 与 I 均有数值（在 evaluation 中）
- `feasibility.key_risks` 是**执行风险**（不要写「实验失败」）
- `evaluation.expected_findings` 是量化预测；`null_result` 是可观测信号
- `finer` 平均 ≥ 3.0 且无单项 < 2
- `stress_test` 含 `preprint_risk`；high 必须在 preprint_risk_reason 写 reframe 路径（**不 cut idea**，保留给用户决策）
- `ai_failure_mode_check.frame_lock` 必填

**Report-level（违反整篇丢弃）**：
- 至少 1 个 `ecosystem_distortion`；至少 1 个 `phenomenon_discovery / hidden_failure_mode`
- 至少 50% SE 相关
- **C1**: `better_solution` 总占比 ≤ 30%
- **C2**: `better_solution × preprint_risk=high` ≤ 1
- **C3**: `new_problem` 总占比 ≥ 40%
- `technical × better_solution` ≤ 20%

**Concession Threshold**（用户 pushback 时）：按 `idea-generation-method.md §7` 打分 → 不到 4 不让步。

**保存后自动校验**：`python3 scripts/validate_idea_report.py output/reports/report_*.json`

---

## 步骤 4：生成报告 JSON

将分析结果组织为以下严格 JSON 结构（所有文字用中文）：

```json
{
  "generated_at": "YYYY-MM-DD HH:MM",
  "source_file": "papers_YYYYMMDD_HHMM.json",
  "total_papers": 整数,
  "analyzed_papers": 整数,
  "executive_summary": "200字以内：今日研究全景、核心趋势、SE领域亮点、值得关注的信号",
  "themes": [
    {
      "name": "主题名（中文，6字以内）",
      "trend": "hot|rising|stable",
      "count_estimate": 整数,
      "description": "60字：这个主题在研究什么、为何重要",
      "keywords": ["词1","词2","词3"],
      "papers": [
        {"title": "...", "url": "...", "source": "...", "published": "..."}
      ]
    }
  ],
  "se_spotlight": {
    "summary": "100字：今日SE领域研究概览，有哪些值得关注的进展",
    "subtopics": [
      {
        "name": "子领域名（如：代码生成）",
        "paper_count": 整数,
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
      "is_se_related": true或false,
      "idea": {"formulation_type":"hypothesis|research_question|proposed_construct","method_type":"empirical_study|technical_contribution|theoretical|vision_position","contribution_form":"new_problem|new_solution|better_solution","one_liner":"≤30字 单句 plain Chinese 禁 jargon 非专家秒懂","approach":"≤120字"},
      "motivation": {"why_matters":"≤80字","signal":{"summary":"≤40字 trigger","source_papers":[{"title":"...","url":"...","source":"..."}]}},
      "novelty": {"novelty_type":"unsolved_problem|research_gap|better_solution","statement":"≤80字","closest_prior_work":[{"title":"...","url":"...","what_they_did":"≤60字","what_we_dont_do":"≤60字"}],"delta_over_prior":"≤80字"},
      "feasibility": {"feasibility_level":"high|medium|low","data_source":"≤60字","effort_estimate":"1人月|3人月|6人月+|12人月+","key_risks":["≤30字 执行风险","≤30字 执行风险"]},
      "evaluation": {"expected_findings":"≤100字 量化预测","null_result":"≤60字 可观测信号"},
      "finer": {"feasible":1-5,"interesting":1-5,"novel":1-5,"ethical":1-5,"relevant":1-5,"average":"X.X"},
      "stress_test": {"strongest_counter":"≤80字","biggest_confound":"≤80字 推理风险","fallacy_risk":"confirmation_bias|hasty_generalization|cherry_picking|survivorship_bias|ecological_fallacy|none","preprint_risk":"high|medium|low","preprint_risk_reason":"≤80字"},
      "ai_failure_mode_check": {"frame_lock":"≤60字（≥1 alternative framing 必）","bug_as_insight":"≤60字或 N/A","shortcut_risk":"≤60字或 N/A"},
      "papers": [{"title":"...","url":"...","source":"...","published":"..."}]
    }
  ]
}
```

---

## 步骤 5：保存报告文件

用 Bash 工具获取当前时间戳，然后用 Write 工具将完整 JSON 保存到：

```
/Users/weima/Documents/crawer_paper/output/report_YYYYMMDD_HHMM.json
```

时间戳格式示例：`report_20260512_1430.json`

---

## 步骤 6：确认

完成后输出：
```
✅ 报告已保存：report_YYYYMMDD_HHMM.json
   共分析 N 篇论文（含 M 篇 SE 相关）
   → 刷新浏览器「研究报告」标签查看：http://127.0.0.1:7860
```

---

## 注意事项

- 全部输出内容使用**中文**
- JSON 中不要有注释，不要有 markdown 代码块包裹
- 如果论文数量充足，themes 至少 6 个，其中 1 个专门命名为「软件工程」或细分子领域
- `se_spotlight` 是对 `themes` 中 SE 相关内容的补充深化，两者可以重叠
- 确保 JSON 格式合法（可用 `python -c "import json,sys; json.load(sys.stdin)"` 验证）
- **`ideas` 单列表必须严格按 `prompts/methodology/idea-generation-method.md` 的 schema 输出**（已合并 opps + sparks）；每条 idea 字段不能缺；C1/C2/C3 三条 better_solution 约束必须满足；用 `scripts/validate_idea_report.py` 校验
