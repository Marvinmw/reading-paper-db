---
name: pilot-experiment
description: 对一条 idea 设计并执行最小可行 pilot 实验——提取可证伪假设，写采集脚本真实运行，用 20-50 样本评估核心信号是否存在（Go/Yellow/Red）。输出 pilot_report JSON + 更新 idea 的 feasibility/expected_findings。触发：「跑一下这条 idea 的 pilot」「帮我验证这个假设」「这条 idea 有没有信号」「先做个小实验看看」「pilot 一下」
---

# Pilot Experiment Skill

## 任务

对指定 idea 设计并执行最小可行验证实验（Mini-Pilot Protocol, MPP），在一次 session 内产出「核心信号是否存在」的 **Go / Yellow / Red** 判断。

**不是完整研究**。目标是：在投入大量人月之前，用 20-50 样本快速确认假设的基本可行性。

---

## 必须先确认（AGENTS.md 协议）

```
准备执行 Pilot Experiment，将使用：

📄 输入：
  - 指定 idea（来自 report JSON / eval JSON / 用户粘贴）
  - prompts/methodology/idea-generation-method.md（了解 evaluation.expected_findings schema）

🛠 Skills 可选启用：
  □ idea-evaluation        （pilot 前后同步更新 FINER / feasibility）
  □ lookback-cross-analysis（需要跨时段样本池时启用）

📋 流程概要：
  Step 1 → 加载 idea + 分类 Pilot 类型（A/B/C/D）
  Step 2 → 形式化假设（Pre-registration，看数据前写好 H0/H1）
  Step 3 → 设计 Mini-Protocol（采样方案 + 标注方案）
  Step 4 → 确认后执行（写脚本 / 调 API / 搜索 / 采集）
  Step 5 → 分析：Go/Yellow/Red 判断
  Step 6 → 保存 pilot_report JSON + 反馈到 idea

⚙ 可用数据源（无需额外凭据）：
  - GitHub Search API（公开仓库，rate limit 60 req/hr 无 token）
  - arxiv API（公开）
  - DBLP API（公开）
  - Semantic Scholar API（公开，500 req/5min）
  - 公开链上数据页面 / 区块浏览器 / DeFiLlama 等开放页面
  - WebSearch + WebFetch（公开页面）
  - 本地 output/papers/*.json（项目 corpus）

✅ 确认开始？请告知：
  - idea 来源（report 文件路径 + index，或粘贴 JSON）
  - 若需要 GitHub token / LLM API key，告知或跳过 Type B
```

---

## 核心原则

| 原则 | 含义 |
|---|---|
| **Minimal** | 20-50 样本足够。追求速度和信号存在性，不追求统计功效 |
| **Executable NOW** | 只用当前 session 工具（Bash/Python/WebSearch/WebFetch/API）|
| **Pre-registered** | H0/H1 在看数据前写好；不能看完数据再改假设 |
| **Honest** | Red 结果 = 有价值输出，不是失败。隐藏负结果会浪费人月 |
| **Fast feedback** | pilot 产出直接 patch 回 idea（feasibility/expected_findings/risks）|

---

## 四类 Pilot 类型

### Type A — 生态测量型（最常见）
**适用**：idea.approach 含「收集 N 个 GitHub/HuggingFace/开源项目 → 测量某发生率」

**协议**：
1. GitHub Search API / arxiv API → 采样 20-30 个符合条件的 target（仓库/论文/commit）
2. 对每个 target 手动/自动标注「是否满足 H1 条件」
3. 计算发生率 ± 标准误；与 expected_findings 的阈值对比

**可运行工具**：`curl` 调 GitHub API / arxiv API，Python 计算统计

**输出核心指标**：`base_rate_estimate`，`n_positive / n_total`，`95ci_lower`

---

### Type B — 实验验证型
**适用**：idea.approach 含「调用 LLM → 测量 FP/FN rate / 对齐效应 / judge 相关性」

**协议**：
1. 从公开 benchmark / trace / 合约仓库 / 事务样本中选 10-20 个有 ground truth 或可人工核验的样本
2. 如 idea 涉及模型/自动分析工具，再调用目标工具或模型；否则直接运行测量脚本
3. 收集输出，与 ground truth 或人工核验结果对比，计算效应大小

**可运行工具**：LLM API（anthropic / openai），Python 脚本计算 Cohen's d / odds ratio

**输出核心指标**：`effect_size`，`cohen_d`，`signal_direction`

---

### Type C — 存在性探测型
**适用**：idea.approach 含「找到 X 现象的真实案例」；idea 需要先证明现象在野外存在

**协议**：
1. WebSearch + WebFetch + GitHub 搜索，找 3-5 个满足 H1 条件的真实存在案例
2. 每个案例记录：来源 URL / 发现方式 / 符合条件的具体证据
3. 评估案例多样性（不同系统/作者/时间）

**可运行工具**：WebSearch / WebFetch / GitHub Search

**输出核心指标**：`existence_cases (list)`，`case_diversity: high/medium/low`

---

### Type D — 原型验证型
**适用**：idea 需要先构建一个测量工具/框架原型才能采集数据

**协议**：
1. 写最小可用脚本（< 150 行 Python）实现 idea 的核心测量方法
2. 在 3-5 个真实样本上运行，记录输出
3. 评估：方法论上可行？输出可解释？

**可运行工具**：Bash / Python + 真实数据输入

**输出核心指标**：`poc_works: true/false`，`precision_on_sample`，`failure_modes`

---

## 流程详解

### Step 1 — 加载 idea + 分类

读取 idea 的以下字段：
- `idea.approach`（核心执行路径）
- `evaluation.expected_findings`（量化预期：阈值 / 效应大小）
- `evaluation.null_result`（null hypothesis 的操作定义）
- `feasibility.data_source`（已声明数据源）
- `feasibility.key_risks`（已知风险）

根据 approach 中的动词决定 Pilot 类型：

| 动词模式 | 类型 |
|---|---|
| 收集 / 采样 / 统计 GitHub / 测量发生率 | Type A |
| 调用 / 测试 LLM / 测量 FP rate / effect size | Type B |
| 找到 / 搜索 / 案例 / 存在性 | Type C |
| 构建 / 实现 / 原型 / 工具 | Type D |

---

### Step 2 — Pre-registration（看数据前完成）

输出格式（必须在 Step 4 之前 commit）：

```
PILOT PRE-REGISTRATION
idea: <title>
pilot_type: <A/B/C/D>
H0: <null hypothesis，具体可操作>
H1: <alternative hypothesis，具体可操作>
primary_metric: <e.g., base_rate / cohen_d / existence_count>
success_threshold: <e.g., base_rate > 0.20 / effect_size > 0.5 / cases ≥ 3>
sample_size: <N>
data_source: <具体来源>
labeling_criteria: <如何判断每个样本是否满足 H1>
```

**反 HARKing 规则**：success_threshold 一旦写下，后续不得因「数据比预期低」而下调。若阈值明显错误，先暂停确认用户再修改。

---

### Step 3 — Mini-Protocol 设计

输出采集方案：
1. **采样语句**：具体的 GitHub Search query / arxiv API 请求 / WebSearch 关键词
2. **过滤条件**：初筛 → 精筛（避免噪声）
3. **标注方案**：每个 sample 判断「Y/N 满足条件」的具体规则（不依赖主观判断）
4. **执行脚本草稿**：给用户确认方案后立刻实现

---

### Step 4 — 执行（真实运行）

**数据采集脚本原则**：
- 保存原始数据到 `output/pilots/raw_<slug>_<ts>.json`（不丢弃原始数据）
- 脚本含进度打印 + 简单 retry（API rate limit）
- 采集结束后，在 session 内立即完成标注（手动标注 ≤ 50 条是可行的）

**可用 API 端点**：
```bash
# GitHub Search（无 token）
curl "https://api.github.com/search/repositories?q=<query>&sort=stars&per_page=30"

# arxiv API
curl "https://export.arxiv.org/api/query?search_query=<query>&max_results=20"

# Semantic Scholar（无 token，500 req/5min）
curl "https://api.semanticscholar.org/graph/v1/paper/search?query=<query>&limit=20&fields=title,abstract,year,citationCount"
```

**降级策略**（当数据不足时）：
| 问题 | 降级 |
|---|---|
| GitHub API rate limit | WebSearch 替代；或提示用户加 `GITHUB_TOKEN` 环境变量 |
| LLM API 无 key（Type B）| 改用 Ollama 本地模型；或降级为 Type C 存在性探测 |
| 公开数据集找不到 | WebFetch 相关 benchmark repo；或手动构造 5-10 样本 |
| 目标系统需登录 | 改用公开 GitHub issue / PR 记录作为代理指标 |

---

### Step 5 — 分析与信号判断

#### Go / Yellow / Red / Gray 标准

| 信号 | Type A | Type B | Type C | Type D |
|---|---|---|---|---|
| **🟢 Go** | base_rate 95% CI 下界 > threshold | Cohen's d > 0.5 或 OR > 2 | ≥ 3 高质量多样案例 | ≥ 4/5 样本成功 |
| **🟡 Yellow** | CI 跨越 threshold / 方向对但弱 | 0.2 < d < 0.5 | 2 案例，低多样性 | 3/5 成功，失败模式可修复 |
| **🔴 Red** | base_rate < threshold 且 CI 上界 < threshold | d < 0.2 或反向 | < 2 案例 | < 2/5 成功 |
| **⬜ Gray** | 标注噪声 > 30% / 样本严重偏差 | 数据集质量问题 | 找不到可信来源 | 脚本无法运行 |

#### Yellow 行为（不等于失败）

Yellow → 分析原因并提供 **pivot 路径**：
- 阈值设太高？→ 建议下调 expected_findings
- 场景太宽泛？→ 建议缩窄到高风险子域（如「仅测 LangGraph 工作流」）
- 数据源质量差？→ 建议换数据源（如从 GitHub → HuggingFace Spaces）
- 核心假设方向对但弱？→ 建议加控制变量分离混淆因素

---

### Step 6 — 输出 pilot_report + 反馈 idea

**保存路径**：`output/pilots/pilot_<idea-slug>_YYYYMMDD_HHMM.json`

**Schema**：
```json
{
  "pilot_id": "pilot_<slug>_<ts>",
  "idea_title": "...",
  "idea_source": "report_YYYYMMDD_HHMM.json#ideas[N]",
  "pilot_type": "A|B|C|D",
  "generated_at": "YYYY-MM-DD HH:MM",

  "pre_registration": {
    "h0": "...",
    "h1": "...",
    "primary_metric": "...",
    "success_threshold": "...",
    "sample_size": 30,
    "data_source": "...",
    "labeling_criteria": "..."
  },

  "execution": {
    "actual_sample_size": 28,
    "collection_method": "GitHub Search API + manual review",
    "raw_data_file": "output/pilots/raw_<slug>_<ts>.json",
    "execution_issues": ["rate limit hit on query 3, waited 60s", "..."],
    "labeling_notes": "..."
  },

  "results": {
    "primary_metric_value": 0.32,
    "confidence_interval": [0.15, 0.49],
    "n_positive": 9,
    "n_total": 28,
    "breakdown": {},
    "surprising_findings": ["...", "..."],
    "data_quality_issues": []
  },

  "signal": "Go|Yellow|Red|Gray",
  "signal_reason": "...",
  "pivot_path": "...",

  "idea_updates": {
    "feasibility_level_update": "high (was medium) | medium (was high) | unchanged",
    "expected_findings_update": "...",
    "key_risks_add": ["..."],
    "closest_prior_work_add": []
  }
}
```

**反馈到 idea**（直接在 report JSON 中 patch 对应 idea 字段）：
- `feasibility.pilot_evidence`：summary of pilot results
- `feasibility.feasibility_level`：如有显著变化则更新
- `evaluation.expected_findings`：若 Yellow → 更新数值预期
- `stress_test.biggest_confound`：若 pilot 暴露新混淆因素 → 补充

---

## 技术限制清单（session 内不可做的事）

| 限制 | 替代方案 |
|---|---|
| 无法运行 Playwright/浏览器 | WebFetch 静态页面；或跳过 UI 交互测试 |
| 无法访问付费 dataset | 找公开替代品或手动构造 mini 样本 |
| LLM API 无 key（Type B）| 降级到 Type C 存在性探测；或用 Ollama |
| 大规模 GitHub 爬取（>100 repos）| 限 30 repos + 标注 → 报告 CI 宽 |
| 人工标注 > 50 条太慢 | 降到 20-30 条，更宽 CI 但仍可判断方向 |

---

## 输出后必做

1. 验证 JSON：`python3 -c "import json,sys; json.load(open('<path>'))"`
2. 若 Red → prepend 到 `prompts/methodology/idea_feedback_log.md` §3，记录 pilot 失败原因
3. 若 Go → idea 的 `feasibility.feasibility_level` 若原为 medium，建议升级为 high，注明 pilot evidence
4. 提示：`output/pilots/pilot_*.json` 在 Web UI 中暂不显示；可在终端 tab 用 `cat` 查看

---

## 用户响应

| 输入 | 行为 |
|---|---|
| 「pilot 这条 idea」 + report 路径 | 加载 idea → Step 1-6 |
| 粘贴 idea JSON | 直接从 Step 1 开始 |
| 「只设计方案，先不执行」 | 完成 Step 1-3，输出 MPP 方案 + pre-registration，等用户确认执行 |
| 「执行 / 开始」 | Step 4-6 |
| 「换 Type C」 | 重设 pilot_type，回到 Step 2 重做 pre-registration |
| 「提供 GitHub token / API key」 | 更新 env，继续执行 |
| 「跳过 patch idea」 | Step 6 只保存 pilot_report，不修改原 report JSON |
