---
description: 任意主题驱动的专项研究报告。Claude 自动提取关键词+子场景，你 review 后跑完整 PI-Code 同款质量门流程。
---

# /topic-report — 主题驱动专项调研

## 参数 (`$ARGUMENTS`)

```
/topic-report <topic description>
```

例：
- `/topic-report distributed transaction`
- `/topic-report blockchain smart contract security`
- `/topic-report DeFi MEV attack`
- `/topic-report query optimization learned index`
- `/topic-report consensus fault tolerance Byzantine`
- `/topic-report zero-knowledge proof blockchain`

支持的可选 flag（附在主题后）：
- `--window 30d` / `--window 60d` / `--window 90d`（默认 90d）
- `--skip-confirm`（跳过 Step 2 关键词确认；危险，主题偏题风险）
- `--gaps`（在 Step 5 输出额外 gap 专项段）

## 你是执行引擎。按以下流程跑：

---

### Step 0 — 确认主题与流程（必须）

输出确认模板等用户回「确认/开始/好」：

```
准备执行 /topic-report，主题：「<topic>」

📋 流程概要：
  Step 1: 加载论文 corpus（窗口: <window>）
  Step 2: 自动提取 10-20 关键词 + 5-9 子场景 → 你 review 调整
  Step 3: 用确认后关键词筛候选 → maturity 分级
  Step 4: top 5-10 信号 paper 真 WebFetch 全文 Limitations
  Step 5: 生成 8-12 idea 含完整 schema
  Step 6: 每个 idea 跑 WebSearch prior（含 new_solution/better_solution）
  Step 7: §2 blacklist 比对 + C1/C2/C3 + validator
  Step 8: 保存 + 浏览器提示

🛡 质量门（不可跳）：
  - prompts/methodology/idea-generation-method.md（idea 5 大字段 + FINER + stress）
  - prompts/methodology/idea_feedback_log.md §2 blacklist
  - WebFetch top 5-10 paper full-text
  - WebSearch arxiv prior 每条 idea 一次
  - scripts/validate_idea_report.py

📊 Tool 预算（估算）：
  - WebFetch: 5-10 次
  - WebSearch: 8-25 次（含 Step 2 关键词扩展 + Step 6 prior search）
  - 总耗时: 10-25 min

📁 输出：output/reports/report_<topic-slug>_<ts>.json

✅ 确认开始？或要调整（如：换窗口 / 改主题 / 跳确认）？
```

---

### Step 1 — 加载论文 corpus

```bash
ls output/papers/papers_*.json
```

读取所有 papers 文件，合并去重（url 或 title 为 key）。

按 `--window` 过滤：
- `30d` / `60d` / `90d`（默认） — 按 `published` 字段过滤（< CUTOFF 的丢弃）

无 published 字段的论文保留（视为最新爬到）。

报告：总篇数 / 去重后 / 窗口过滤后 / 各来源分布。

---

### Step 2 — 自动提取关键词 + 子场景（user 确认）

**对主题做 2 件事**：

#### 2a. 关键词扩展（10-20 个）

基于主题语义，**用你（Claude）自己的领域知识** 生成关键词候选，分两组：

- **核心 arm**（5-10 个）：主题最直接的同义词 + 缩写。如「RAG 安全」→ `rag`, `retrieval-augmented`, `knowledge base poisoning`, `vector db attack`, `passage injection`, ...
- **关联 arm**（5-10 个）：定义攻击面的 modifier。如对 RAG 安全 → `embedding poisoning`, `corpus injection`, `passage selection`, `oracle poisoning`, ...

#### 2b. 子场景提议（5-9 个）

基于主题 + 当前 corpus 中真实存在的论文，提议 5-9 个子场景命名。每个子场景给：
- 名称（≤8 字）
- 判断标准（关键词组合）
- corpus 估计命中数（grep 后估）

#### 2c. 输出确认提示

```
🔍 我提议的关键词 + 子场景（你 review）：

📍 核心关键词 ({N})：
  prompt injection / IPI / jailbreak / ...

📍 关联关键词 ({M})：
  agent attack / data plane / observability / ...

📍 子场景 ({K})（含 corpus 命中估计）：
  1. <name1> — (kw1 + kw2)  [估 ~20 篇]
  2. <name2> — (kw3 ∧ kw4)  [估 ~12 篇]
  ...

✅ 全部 OK 直接「确认」/ 要改说「加 X / 删 Y / 改 Z」/ 要重新提议说「重提」

⚠ 若 --skip-confirm 则跳此步直接用候选关键词
```

用户确认后写入 `/tmp/<topic-slug>_keywords.json` 给后续 step 用。

---

### Step 3 — 筛选 + maturity

用 Step 2 确认的关键词跑筛选。判定：
- 命中**核心 arm + 关联 arm 各 1 个** → 候选
- 仅命中核心 arm（强信号词，如「prompt injection」） → 也候选
- 仅命中关联 arm → 看具体情况，倾向不收

对候选按子场景多标签分类。每个子场景算 maturity：
- **饱和(saturated)**：≥15 篇 且 时间跨度 ≥6 个月
- **活跃(active)**：8-14 篇 或 近 3 月内有论文
- **新兴(emerging)**：4-7 篇 且 集中近 3 月
- **空白(blank)**：< 4 篇

---

### Step 4 — Top 5-10 信号 paper full-text WebFetch

按 relevance score（关键词命中数 + recency）排序，取 top 10。

对每篇 paper：
```
WebFetch https://arxiv.org/html/<id>
prompt: "Extract Limitations / Discussion / Future Work / Threats to Validity verbatim. List 3 concrete unresolved problems with quotes."
```

抓不到 HTML render（404）→ 重试 `/html/<id>v1`；仍失败 → skip 这篇用 abstract anchor。

抽取的 "author-stated gap" 是 idea 的核心 anchor。

---

### Step 5 — 生成 8-12 ideas（按 idea-method 5 大字段）

每条 idea 必填：
- `idea`：formulation_type / method_type / contribution_form / one_liner ≤30 字 / approach
- `motivation`：why_matters + signal（含 source_papers）
- `novelty`：novelty_type + closest_prior_work[].what_they_did + what_we_dont_do + delta
- `feasibility`：level + data_source + effort_estimate + key_risks
- `evaluation`：expected_findings（含数值）+ null_result
- `finer`：5 项 ≥ 2 + avg ≥ 3.0
- `stress_test`：counter + confound + fallacy_risk + preprint_risk (+reason 若 high)
- `ai_failure_mode_check`：frame_lock（必填，含 alternative framing）

**优先从 Step 4 抽到的 author-stated gap 反推 idea**，避免 abstract pattern matching。

---

### Step 6 — WebSearch prior（每条 idea）— **soft warning，不 cut**

每条 idea 跑 1 次 tighter WebSearch：
```
arxiv 2026 <idea title 主词> <一个同义词> <一个 specific 修饰词>
```

判定（**全部保留 idea**，仅标 risk + 写 differentiation；不自动降级也不 cut）：
- **HARD collision**：≥1 篇 same-month direct prior → `preprint_risk=high` + closest_prior_work 必写 differentiation + preprint_risk_reason 写 reframe 退路（vision/synthesis/paradigm）
- **MEDIUM**：partial overlap → `preprint_risk=medium` + closest_prior_work 写 differentiation
- **LOW**：仅 methodology 借鉴 → `preprint_risk=low`

**用户裁决原则**：所有 collision 信息**透明展示在 report 里**——你自己看 prior 强度后决定 keep / pivot / drop。我**不替你 cut**。

---

### Step 7 — §2 Blacklist + C1/C2/C3 + Validator

#### 7a. §2 Blacklist 软警告（全保留 idea）
Read `prompts/methodology/idea_feedback_log.md` §2。每条 idea 比对：
- 命中 saturated 行 → 在 closest_prior_work 标注 + 写 differentiation
- 命中 B2 反 pattern → 在 stress_test.fallacy_risk 标注 + preprint_risk 提高
- **不自动 cut，不自动降级 contribution_form**——让用户看到完整 candidate pool

#### 7b. Report-level 约束
- **C1**: `better_solution` 占比 ≤ 30%
- **C2**: `better_solution × preprint_risk=high` ≤ 1
- **C3**: `new_problem` 占比 ≥ 40%
- `technical × better_solution` ≤ 20%
- 至少 1 个 `ecosystem_distortion`
- 至少 1 个 `phenomenon_discovery` / `hidden_failure_mode`
- SE 相关 ≥ 50%（若主题 SE 相关；否则放宽）

#### 7c. Validator
```bash
python3 scripts/validate_idea_report.py output/reports/report_<topic-slug>_<ts>.json
```

不过 → 报 violations + 部分产出留盘。

---

### Step 8 — 保存

JSON schema：
```json
{
  "generated_at": "YYYY-MM-DD HH:MM",
  "report_type": "topic_analysis",
  "topic": "<原始 topic>",
  "topic_slug": "<lowercase-dash-30char-max>",
  "window": "30d|60d|90d",
  "keywords": {"core": [...], "related": [...]},
  "total_scanned": N,
  "total_matched": M,
  "executive_summary": "200 字",
  "landscape": [{"scenario","maturity","paper_count","summary","key_works":[],"saturation_reason","opportunity"}],
  "themes": [{"name","trend","count_estimate","description","keywords":[],"papers":[]}],
  "top_papers": [{"title","url","source","published","reason","why_notable"}],
  "ideas": [<full schema>],
  "gap_analysis": {"saturated_scenarios":[],"emerging_scenarios":[],"blank_spots":[]}
}
```

**文件名**：
```
output/reports/report_<topic-slug>_<YYYYMMDD_HHMM>.json
```

`topic-slug` 规则：
- 小写 + 下划线/空格 → `-`
- ASCII 化（中文 → pinyin 或保留原汉字皆可，保留原汉字简单些）
- 最长 30 字符
- 例：「RAG 安全」→ `rag-anquan` 或 `rag-security`；「prompt injection × code agent」→ `pi-code-agent`

---

### Step 9 — 最终汇报

```
✅ /topic-report 完成
   📁 outputs:
      - report: report_<topic-slug>_<ts>.json (M ideas, FINER avg <X.X>)
   📊 stats:
      - Topic: <topic>
      - Window: <window>
      - Corpus matched: <N>/<total>
      - Ideas: <new_problem> NP / <new_solution> NS / <better_solution> BS
      - WebFetch: F  WebSearch: S
      - C1/C2/C3 status: PASS / VIOLATED
   🌐 http://127.0.0.1:7860「研究报告」标签
```

---

## 注意事项

1. **主题驱动 ≠ keyword matching only**：Claude 的领域知识在 Step 2 自动扩展关键词，不能只取主题字面词。
2. **subscene 命名不要复用 PI×Code 的**：每次按 corpus 实情提议。如「agent memory」主题不会有「CI/CD」子场景。
3. **§2 blacklist 是跨主题通用的**：饱和判定是基于 prior，不分主题。
4. **失败必停**：Step 1-7 任一失败 → 停 + 报错位置 + 部分产出留盘。
5. **Tool 预算超 50 WebSearch** → 主动停 + 提示主题可能空间饱和。
6. **slug 不能撞**：若 `report_<slug>_<ts>.json` 已存在同 ts → 加秒。

当前参数：$ARGUMENTS
