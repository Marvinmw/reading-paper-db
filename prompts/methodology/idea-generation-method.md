---
name: idea-generation-method
description: 每日报告 idea 生成方法论。5 大字段（idea/motivation/novelty/feasibility/evaluation）+ FINER 评分 + stress_test + AI 失败模式自检。idea 用 plain language 区分 hypothesis / research_question / proposed_construct 三种 framing。
---

# Idea Generation Method（每日报告专用）

> reviewer 看 idea 的顺序：**idea → motivation → novelty → feasibility → evaluation**。每项都要回答 + 写出来。

---

## 0. 三个最容易混淆的区分

### 0.1 Idea ≠ Hypothesis ≠ Claim

| 概念 | 含义 | 谁来写 |
|---|---|---|
| **Idea** | 最广的概念——我们想研究什么。可以是假设、开放问题、新提出的概念 | idea 阶段（pre-experiment）|
| **Hypothesis** | 可测的预测命题（"我们假设 X 比 Y 高"）| idea 阶段，但仅当我们愿意预测时 |
| **Research Question** | 开放问题，不预测答案（"X 与 Y 关系如何？"）| idea 阶段，探索型 |
| **Proposed Construct** | 提出一个新概念/分类/威胁模型 | idea 阶段，定义型 |
| **Claim** | 实验做完后、有证据支持的断言 | **paper conclusion**，不是 idea 阶段 |

所以 idea 阶段写 `idea.formulation` 时，先选一个 `formulation_type`（hypothesis / research_question / proposed_construct），别一上来就 "claim"。

### 0.2 `idea.formulation` 里不写数值

数值（ASR、effect size、比例、阈值）全部放 `evaluation.expected_findings + null_result`。

| 字段 | 含数值？ | 例 |
|---|---|---|
| `idea.formulation`（hypothesis）| ❌ 只说方向 | "我们假设 separation 范式在真实部署下系统失效" |
| `evaluation.expected_findings` | ✅ 具体数字 | "4 个 SOTA defense 在 contextual 类下 ASR 均 ≥ 60%" |
| `evaluation.null_result` | ✅ 反向数字 | "至少 2 个 defense ASR < 30%" |

idea 阶段写数值 = 伪造证据，reviewer 一眼看穿。

### 0.3 `motivation.signal` ≠ `idea.formulation`

| 字段 | 时间 | 内容 |
|---|---|---|
| `signal` | 过去 | 今日哪篇论文/反常**激发**了 idea（trigger）|
| `formulation` | 将来 | 我们**要研究**的命题/问题/概念 |

signal 是起点（"什么让我们想到这个"），formulation 是终点（"我们想搞清楚什么"）。两者一致 = 抄 prior work。

### 0.4 `feasibility.key_risks` ≠ `stress_test.biggest_confound`

| 字段 | 关注 | 例 |
|---|---|---|
| `key_risks` | 能不能做完（执行风险）| "API 限速"、"数据闭源"、"标注成本高" |
| `biggest_confound` | 做完后结论是否成立（推理风险）| "效应可能来自 dataset artifact" |

### 0.5 一句话规则（最重要的硬约束）

**`idea.one_liner` 必须是一句话能让非专家秒懂的总结。** 这是 idea 的核心字段。

| 规则 | 要求 |
|---|---|
| 长度 | ≤ 30 字（中英混合按视觉长度算） |
| 句数 | **1 句**（不能用"——""——""；"分多句）|
| 语言 | plain Chinese，禁 jargon（见下方黑名单） |
| 主语 | 现象/失败/假设/问题类/方法本身——不是工具名 |
| 测试 | **念给一个不熟悉这个 paper 的同行听，他能秒懂吗？** 不能 = 重写 |

#### Jargon 黑名单（出现 ≥ 1 个就重写）

| 类别 | 禁用词（示例）| 改成 |
|---|---|---|
| 学术腔 | 范式 / 系统性 / SOTA / mainstream / paradigm-level | 主流 / 都 / 普遍 |
| 抽象动词 | 失效 / 偏移 / 折叠 / 失真 / 漂移 | 防不住 / 走样 / 失败 / 越来越糟 |
| 包装词 | XX 化 / 通用化 / 形式化 / 系统化 | 直接描述对象 |
| 多层修饰 | 「在真实部署下系统性失效」| 「在真实环境都防不住」|
| 中英混拼专业术语 | "data-instruction separation 范式" | "把指令和内容分开的防御思路" |

**例外**：领域核心名词允许保留（prompt injection / MCP / Agent / RL）——它们是研究对象本身。

#### 对照

| ❌ 长 + jargon | ✅ One-liner |
|---|---|
| "我们假设 Data-instruction separation 作为 PI 防御主流范式在真实部署下系统性失效——所有 SOTA separation-based defense 在 contextual manipulation 类攻击下均无法有效防御" | "主流 prompt injection 防御对藏在内容里的指令全都防不住" |
| "我们提出一类新攻击面「Pipeline Backdoor」——通过 LLM 部署管线（编译/位置编码/fine-tune adapter/量化/serving runtime）触发，与传统 data-poisoning backdoor 在攻击机制和 detection 信号上正交" | "我们提出一种新后门：不动训练数据，只动 LLM 部署管线" |
| "我们假设 MCP server 生态中单个 taint-style 漏洞通过 tool cloning 在 downstream 间显著放大；传统 CVE advisory 在 fork 模式下失效" | "MCP 工具被大量抄袭复制，一个漏洞会跟着复制扩散到全网" |

**核心**：reviewer abstract 阶段就是看 one_liner。读不懂 = 进不了下一轮。

### 0.6 Preprint Extension Risk（最大 incremental 陷阱）

「延续近期 preprint」是最隐蔽的 incremental trap：

```
我们花 6 个月做 prior 的 +1 延续
  ↓
prior preprint 被某顶会接受（往往就是 ICSE/CCS/NeurIPS）
  ↓
我们的「+1 delta」沦为对方论文的 baseline
  ↓
related work 一句 "concurrent" 就把我们淡化
  ↓
reviewer 打 incremental contribution 低分
```

**触发条件**：当 `closest_prior_work` 全是 2025-2026 preprint 且我们的 delta 是「+N→+N+1」级扩展（如 "他们 1 个 defense，我们 4 个"）时，**preprint_risk 至少 medium**。

**reframe 路径**（high preprint_risk 必填，**不自动降级也不 cut**——idea 保留给用户决策）：
1. **reframe 为 new_problem**：不是 extension 而是新视角/新现象
2. **paradigm-level 升级**：不是 N+1 测量，而是 paradigm 失效证明
3. **multi-prior cross-synthesis**：综合多个独立 prior 形成它们各自看不到的洞察
4. **transparent 保留 + 标 risk + 让用户判断**——这是默认行为

**优先级**：new_problem > new_solution > better_solution

**最稳组合**：empirical_study × new_problem
**最危险组合**：technical_contribution × better_solution（纯 N+1 优化）

每个 idea 在 `stress_test.preprint_risk` 显式打分（high/medium/low）+ 写理由。high risk 必须在 reason 里写 reframe 路径——但 idea 本身**始终保留**，不自动 cut 也不自动降档 contribution_form。

### 0.4 Full-Text 阅读顶 paper（不只 abstract）

**问题**：仅靠 paper title + abstract 推 idea = pattern matching，产出永远是 N+1。

**实操**：
1. 信号扫描阶段先按 abstract 筛 top 5 信号 paper
2. **强制 WebFetch 这 5 篇的完整 PDF**（不是只 abstract）
3. 抽取每篇的：
   - **Limitations 节** — 作者自报短板
   - **Discussion / Future Work 节** — 作者自留 gap
   - **Threats to Validity / Caveats** — 作者承认的不确定性
4. 这些 section 是 **author 明确告诉你 "I didn't solve this"**——比 abstract gap 高质量 10×

**用法**：
- idea 的 `signal.summary` 引用具体 paper 的 Limitations 行号 / 段落
- `closest_prior_work[].what_we_dont_do` 引用 author 自承的 unresolved 点
- 没读 full-text 的 idea，preprint_risk 自动 +1 档（因为可能 prior 在 Discussion 已提）

**例**：Overeager Coding Agents paper 的 §6 Discussion 里如果作者自己说 "we don't measure taxonomy of overeager actions"，那「Overeager 越权 Pattern taxonomy」就是 trivial follow-up——读完 full-text 就能避免误标为 new_problem。

---

### 0.5 Feedback Log 必读（防再犯）

**问题**：同样的错误反复犯（misclass new_problem / 漏 prior / 误标 preprint_risk low）。

**实操**：
- 任何 idea 生成任务**开始前必须 Read** `prompts/methodology/idea_feedback_log.md`
- §2 blacklist 是模式黑名单——逐条比对 candidate idea
- 命中 blacklist 项 → 在 closest_prior_work 写 differentiation + preprint_risk 提高（**不 cut**，保留给用户决策）
- 任务结束后用户给 rejection 反馈 → 我 prepend §3 history + 提炼到 §2

这是「负面经验」固化机制，与 validator（正面 schema 校验）互补。

---

### 0.6 Starting Point Validity（**生成前必做，最先检查**）

> "好 idea 的 50% 来自起点是否站得住。起点不稳，后面全部是沙上建塔。" — Idea 0 事故教训

**Idea 的 starting point** = 触发这条 idea 的那个 observation / phenomenon / gap。它是整个 idea 的地基；地基垮则 idea 无论多精巧也不可行。

#### 三个必检问题（生成/评估任何 idea 前先跑）

| 检查 | 问题 | 通过条件 |
|---|---|---|
| **SP-1 主干性** | 这个观察来自 source paper 的**主要发现**，还是 footnote / Limitations / 附带提及？| 必须来自 main finding / 核心数据 / central claim。Limitations/footnote/side note 的观察只能作为 motivation，不能作为 phenomenon 本身 |
| **SP-2 可操作性** | 这个 starting point 的核心概念可以在不循环的情况下操作化（定义 + 测量方案）吗？| 必须能写出明确的测量方案，不依赖「假设我们已经知道 X」，不产生 circular reasoning |
| **SP-3 作者态度** | Source paper 的作者**自己是否已经放弃这个方向**？（"resists quantification"、"we were unable to reliably measure"、"future work suggests caution"）| 若作者已放弃 → 需要 **独立理由说明为何我们能做**，若无理由则 cut |

#### 典型危险信号（任一命中 → 暂停，检查三问）

- Starting point 来自 paper 的 Limitations 节、Discussion 末尾、or 脚注
- 原文包含「this resists quantification」「we lacked ground truth」「we cannot reliably distinguish」
- Idea 的核心 phenomenon 和「正常行为」之间没有清晰的判别边界
- Starting point 依赖于「用 LLM 自动标注 X」，而 X 的定义本身就需要 LLM 才能判断（循环）
- Source paper 的关键数字来自单 case study，不具普遍性

#### 起点评级（必须在 idea schema 中标记）

| 等级 | 含义 | 对应行动 |
|---|---|---|
| `SP_solid` | 主要发现 + 可操作 + 作者未放弃 | 正常推进 |
| `SP_weak` | 次要发现 or 可操作性存疑 + 有改进路径 | 标注 + 说明为何仍可做；FINER Feasible 上限 3 |
| `SP_invalid` | footnote/Limitations/作者放弃 + 无独立可操作方案 | **必须 cut**，不进入完整评估流程 |

**事故案例 (2026-05-27)**：Idea 0「anosodiaphoria 发生率」起点来自 Universal Cliff (2605.26174) 一个脚注观察，原作者明确表示「resists quantification」（auto-judge 精度 17-50%）后放弃量化。核心概念（scratchpad 压制 vs 正常推理修订）无法区分 → SP_invalid → cut。

---

### 0.65 Prior-Art 真实搜索（new_problem 强制）

**所有标 `contribution_form = new_problem` 或 `novelty_type = unsolved_problem` 的 idea**，在 commit 前必须：

1. 用 `se-literature-search` skill（playbook）真去 **arxiv + OpenAlex** 两源搜：
   - title 主词
   - 同义词组 / 近邻概念
   - 关键技术词
2. 检查近 **6 个月** preprint
3. 若有直接 prior（warning-only，**不自动 cut，不自动降级**）：
   - 升 `preprint_risk` → `high`
   - 在 `closest_prior_work` 加该 paper + 写 differentiation
   - 加 `novelty_after_review` 字段
   - 在 `preprint_risk_reason` 写 reframe 路径
   - contribution_form **保留作者本意** —— 让用户读完 collision 信息后决定 keep / pivot / drop

**为什么**：本项目 `output/papers/` 内 corpus 是历史爬取 snapshot，**不与 arxiv 实时同步**。仅在本地 grep = 必漏掉同月新 preprint。

**事故案例 (2026-05-23)**：idea「CI/CD Agentic Workflow Injection」标 new_problem + preprint_risk=low；用户递来 Wang et al. arXiv 2605.07135 "Demystifying and Detecting Agentic Workflow Injection Vulnerabilities in GitHub Actions" — 100% 直接 prior。我未做真实 search 就标 new_problem，结构性失败。

**实操**：每个 new_problem idea 至少跑 1 次 `se-literature-search`，把搜索 query + 结果摘要写入 idea 的 `novelty.search_evidence` 字段（新增可选字段）。

---

### 0.7 better_solution 三条硬约束（防 incremental 通货膨胀）

`better_solution` 是 contribution_form 三类中**最 incremental** 的（已有问题 + 数值更好），即使搭配 empirical_study 也容易沦为「+N→N+1」延续。三条数量约束防止它膨胀：

| 约束 | 数值 | 含义 |
|---|---|---|
| C1: `better_solution` 总占比 | **≤ 30%** | 不分 method_type；防止全报告变成"调参 + 延续"|
| C2: `better_solution × preprint_risk=high` | **≤ 1**（或必须 reframe） | 高 preprint 风险的 incremental 至多 1 条 |
| C3: `new_problem` 总占比 | **≥ 40%** | 强制至少 40% 是真正的新主张 |

**违反时的标准动作**：
- 违 C1 → 砍 incremental 最严重的 better_solution，或 reframe 1-2 条为 new_solution / new_problem
- 违 C2 → 把 high preprint risk 的 better_solution 强制 reframe（升级为 paradigm-shift / cross-paper synthesis / vision paper）
- 违 C3 → 增加 new_problem idea，或砍 better_solution 让占比相对上升

**校验**：用 `scripts/validate_idea_report.py <report.json>` 一次性 hard check。

---

## 1. 六类 strategy（一览）

| Strategy | 一句话 | 推荐 formulation_type |
|---|---|---|
| `phenomenon_discovery` | 命名 + 首次系统化记录一个现象 | hypothesis 或 research_question |
| `hidden_failure_mode` | 揭示一类被忽略的失败 | hypothesis |
| `assumption_break` | 证明某默认假设不成立 | hypothesis |
| `ecosystem_distortion` | 测真实生态对基础机制的偏离 | hypothesis 或 research_question |
| `new_problem_class` | 提出新攻击面 / 新问题类 | **proposed_construct** |
| `better_solution` | 已知问题 + 数值上更好的新方法 | hypothesis |

`novelty_type` 与 strategy 的常见配对：
- phenomenon / hidden_failure / ecosystem → research_gap
- assumption_break / new_problem_class → unsolved_problem
- better_solution → better_solution

---

## 1.6 两条正交分类轴（method × contribution）

`strategy` 描述 claim 怎么 framing。但 idea 本质属性还有两条正交轴需要单独标：

### Axis A: `method_type`（研究方法/论文类型）

| 类型 | 含义 | 典型 strategy |
|---|---|---|
| `empirical_study` | 测量/实证/生态级研究 | phenomenon / hidden_failure / ecosystem / assumption_break |
| `technical_contribution` | 算法/系统/工具/method | new_problem_class / better_solution |
| `theoretical` | 定理/证明/复杂度分析 | assumption_break / new_problem_class |
| `vision_position` | 观点 paper / call to action | new_problem_class（CIDR/SOSP vision track） |

### Axis B: `contribution_form`（贡献形式）

| 类型 | 含义 | 例 |
|---|---|---|
| `new_problem` | 首次定义、命名、formulate 一个 well-defined 问题 | ProcBench / Library Drift / Pipeline Backdoor |
| `new_solution` | 已有问题上新方法 + 显著 insight | Agentic Model Checking / VIPER-MCP |
| `better_solution` | 已有问题更好 motivation + 更好方案 | 任何 SOTA 改进 paper（最 incremental） |

### Robustness 排名（按对 preprint 风险的抵抗）

| method × form 组合 | 例 | preprint 抗性 |
|---|---|---|
| **empirical × new_problem** | ProcBench / Library Drift | 🟢 最高 |
| technical × new_problem | VIPER-MCP / Pipeline Backdoor | 🟢 高 |
| empirical × new_solution | 大规模新方法对比 | 🟡 中 |
| technical × new_solution | 新算法解新角度 | 🟡 中 |
| empirical × better_solution | 大规模重测旧方法 | 🟡 中 |
| **technical × better_solution** | 优化已知 baseline | 🔴 低（纯 incremental） |

### 报告整体约束
- 至少 1 个 `contribution_form = new_problem`
- `technical × better_solution` ≤ 20% 总 idea 数
- preprint_risk = high 的 idea 必须在 reason 里写明 reframe 路径（不弃用，保留给用户决策）

---

## 2. 如何识别每类 strategy（方法论级）

每类都按 **三步诊断 + 扫描启发 + 接受门** 给出操作指南。

### 2.1 `phenomenon_discovery`（现象发现）

#### 三步诊断
1. **找一个稳定可观察的现象** — 多个独立来源（论文/issue/bug report）描述同一行为
2. **判断是否已有命名** — 文献里没有清晰 label；否则它已存在，不算 discovery
3. **写一句话 mechanism 假设** — 不要求验证，但要给一个 plausible 解释

#### 扫描启发
- 论文 abstract 出现「surprisingly / unexpectedly / counterintuitively」——是 surprise 还是新现象？
- 多个独立 framework 都出现的同类行为，能否归纳命名？
- 行为有清晰边界（什么时候发生，什么时候不发生）吗？

#### 接受门
- 现象有清晰命名（新词 OR 重命名）
- 不是单 case，能给出**普遍性**（哪怕只是定性观察）
- 至少 1 条 mechanism 假设

#### 推荐 formulation_type
- 有清晰预测时 → `hypothesis`（"我们假设现象 P 在 Y 中普遍存在"）
- 还在探索时 → `research_question`（"现象 P 在 Y 中以怎样的模式出现？"）

#### 历史样本
Library Drift / Sleeper Channels / Overeager Coding Agents / Oracle Poisoning

---

### 2.2 `hidden_failure_mode`（隐藏失败）

#### 三步诊断
1. **找一类失败 F** — 系统中存在但未被命名/未被测量的失败
2. **大规模证据** — F 在多 deployment / 多 system 中都出现
3. **结构性 root cause** — 不止是工程 bug，要有结构性解释（架构 / 评测设计 / 假设错误）

#### 扫描启发
- 现有 benchmark 只测某 metric，是不是有一类失败被遗漏？
- 多 framework / 多 system 都遇到的奇怪行为，能归为一类吗？
- 用户/开发者抱怨频繁但学术没人研究的 failure？

#### 接受门
- F 此前未被命名 / 未被系统化测量
- 大规模证据（不是单 case reproduce）
- 有结构性解释

#### 推荐 formulation_type
- `hypothesis`（"我们假设失败类 F 在 X 类 deployment 中普遍存在"）

#### 历史样本
ProcBench（process-level defect）/ Refusal Evaluation Review（13 corpora 互不通约）/ Multi-agent silent conflict

---

### 2.3 `assumption_break`（假设证伪）

#### 三步诊断
1. **找假设 A** — 被领域**显式**默认、广泛接受的前提（能引文档/标准/教科书）
2. **找反例条件 C** — 在什么条件下 A 不成立
3. **大规模反例** — 用对照实验或大样本观察提供 A 失败的证据，不是 strawman

#### 扫描启发
- 「大家都认为 X，所以...」——X 真成立吗？
- 主流 defense / method 论文常用的 baseline 假设——还成立吗？
- 最 popular framework 的 default 设计是不是从没人挑战？

#### 接受门
- A **显式被默认**（不是 strawman）
- 反例必须是对照实验或大样本（不是单 case）
- 给出 C 的边界（A 在哪些条件下仍成立）

#### 推荐 formulation_type
- `hypothesis`（"我们假设默认假设 A 在条件 C 下不成立"）

#### 历史样本
AI Agents May Always Fall for PI（separation 范式失效）/ Trusted Weights Treacherous Optimizations（compilation semantic 等价）/ Web Agents Should Adopt Plan-Then-Execute（ReAct default）

---

### 2.4 `ecosystem_distortion`（生态失真）

#### 三步诊断
1. **定位机制 M** — 被显式标准化 / 文档化 / 社区默认的基础机制（RFC、库规范、协议、官方教程示例）
2. **观察真实使用** — 大规模真实部署里 M 如何被使用、继承、集成（GitHub 大样本、生态监测、CVE 历史）
3. **量化 gap** — 「设计意图」与「真实使用」的偏差是结构性还是个例？

#### 扫描启发
- 机制 M 的**前置条件**在真实使用中成立吗？（如「输入已 sanitize」）
- 机制 M 的**调用顺序**被遵循吗？（如「先 check 再 transfer」）
- 机制 M 的**属性**随系统演化保持吗？（继承、复用、包装、升级、跨域）
- M 的**漏洞/缺陷**随依赖、复制、分叉传播吗？
- M 的**责任归属**在多层系统中被模糊化吗？

#### 接受门
- M **显式被默认**（能引文档/标准）
- 测量样本**大规模真实**（> 100 真实样本是 baseline）
- gap **结构性**（不只是个例 bug）
- 必须有**可观测后果**（CVE 数、性能损失、合规违规、攻击成功率）

#### 推荐 formulation_type
- `hypothesis`（"我们假设机制 M 在生态 E 中被广泛偏离"）
- 或 `research_question`（"生态 E 对机制 M 的偏离模式是怎样的？"）

#### 历史样本
真实 ecosystem_distortion 论文形式很多样，无固定模板——靠上面三步诊断 + 五条扫描启发即可识别。

---

### 2.5 `new_problem_class`（新问题类）

#### 三步诊断
1. **定义 construct C** — 新的攻击面 / 失败类 / 工程问题，此前不存在的概念
2. **真实 PoC** — C 在真实系统上 work，不只 toy example
3. **影响范围估计** — C 在多少系统 / 部署里可达？量化估计

#### 扫描启发
- 新 API / 协议 / 工具 / dataset 是否打开了新攻击面？
- 多个独立 issue / bug report 是否暗示一类未命名的问题？
- 新硬件 / 新架构是否带来新故障模式？

#### 接受门
- C **此前不存在**（不能是旧问题换名）
- PoC 必须在**真实系统**上 work
- 有**量化影响范围**估计

#### 推荐 formulation_type
- **`proposed_construct`**（"我们提出 C 作为一类新的攻击面 / 问题类"）
- 不是 hypothesis（因为是定义 + 存在性，不是预测）

#### 历史样本
VIPER-MCP（MCP server taint vulns）/ Payload-less Skills / Hidden in Memory（Sleeper Memory Poisoning）/ Pipeline Backdoor

---

### 2.6 `better_solution`（更好的方法）

#### 三步诊断
1. **定义问题 P + baseline M** — 明确已知问题 + 现有 SOTA
2. **量化限制 L** — M 在 benchmark B 上**已被实证的具体数值**（如「ASR 60%」「F1 0.5」）
3. **给出新方法 M' 的 mechanism** — 为什么 M' 在 B 上能改进（不能只说「用了 LLM」）

#### 扫描启发
- SOTA 在哪个 benchmark / metric 上明显不足？
- 多篇论文都报告同类 limitation——是否有更好方法？
- 新机制（RL / mechanism interpretation / 新数据源）能否解决旧问题？

#### 接受门
- L **已被实证**（不是「不行」是「ASR 60%」具体数字）
- M' 给**机制级解释**（不只「用了 LLM」）
- I 的预测**可在 B 上 fairly compare**（具体数值）

#### 推荐 formulation_type
- `hypothesis`（"我们假设方法 M' 在 benchmark B 上比 M 提升 I"）

#### 历史样本
典型 ICSE / NeurIPS technique paper

---

## 3. Schema（强制字段）

```json
{
  "title": "≤15字（主语是现象/失败/假设/问题类/方法，不是工具名）",
  "strategy": "phenomenon_discovery|hidden_failure_mode|assumption_break|ecosystem_distortion|new_problem_class|better_solution",
  "is_se_related": true|false,

  // 0. STARTING POINT：起点有效性（生成/评估最先填，invalid = cut）
  "starting_point": {
    "sp_rating": "SP_solid | SP_weak | SP_invalid",
    "source_type": "main_finding | secondary_finding | limitation | footnote | user_observation",
    "operationalizability": "≤60字：如何不循环地定义 + 测量 starting point phenomenon",
    "author_stance": "pursuing | neutral | abandoned（原作者对此方向的态度）",
    "sp_invalid_reason": "（仅 SP_invalid 填）≤60字：为何 cut"
  },

  // 1. IDEA：我们想研究什么
  "idea": {
    "formulation_type": "hypothesis | research_question | proposed_construct",
    "method_type": "empirical_study | technical_contribution | theoretical | vision_position",
    "contribution_form": "new_problem | new_solution | better_solution",
    "one_liner": "≤30字 单句 plain language（禁 jargon，非专家秒懂）。Hypothesis: '主流 XX 防不住 YY'；RQ: 'XX 和 YY 的关系如何？'；Construct: '我们提出新概念 XX'",
    "approach": "≤120字：怎么做（方法/数据/对照设计的高层描述）"
  },

  // 2. MOTIVATION：为什么重要
  "motivation": {
    "why_matters": "≤80字：解决之后能做什么 / 避免什么风险",
    "signal": {
      "summary": "≤40字：今日哪个论文/反常激发了这个 idea（trigger）",
      "source_papers": [{"title","url","source"}]
    }
  },

  // 3. NOVELTY：新在哪里
  "novelty": {
    "novelty_type": "unsolved_problem | research_gap | better_solution",
    "statement": "≤80字：具体新在哪里",
    "closest_prior_work": [
      {"title","url","what_they_did":"≤60字","what_we_dont_do":"≤60字"}
    ],
    "delta_over_prior": "≤80字（必须具体，禁'更好''更全面'）"
  },

  // 4. FEASIBILITY：能不能做（执行层面）
  "feasibility": {
    "feasibility_level": "high|medium|low",
    "data_source": "≤60字",
    "effort_estimate": "1人月|3人月|6人月+|12人月+",
    "key_risks": ["≤30字 执行风险1","≤30字 执行风险2"]
  },

  // 5. EVALUATION：怎么验证（量化预测）—— idea 阶段必填
  "evaluation": {
    "expected_findings": "≤100字：QUANTITATIVE — 数值/比例/effect size 都在这",
    "null_result": "≤60字：QUANTITATIVE — 观察到什么数字就说明 formulation 不成立"
  },

  // 6. FINER 评分
  "finer": {
    "feasible":1-5, "interesting":1-5, "novel":1-5,
    "ethical":1-5, "relevant":1-5, "average":X.X
  },

  // 7. STRESS TEST（mini Devil's Advocate）
  "stress_test": {
    "strongest_counter": "≤80字：reviewer 最可能的攻击点",
    "biggest_confound": "≤80字：结论可能的替代解释（推理风险）",
    "fallacy_risk": "confirmation_bias|hasty_generalization|cherry_picking|survivorship_bias|ecological_fallacy|none",
    "preprint_risk": "high | medium | low",
    "preprint_risk_reason": "≤80字：若 closest_prior_work 6 月内被某顶会接受，我们的贡献是否退化为 baseline / related-work-mention？high 必须写 reframe 路径（reframe/paradigm-shift/multi-prior-synthesis）——idea 仍保留，由用户决定 keep/pivot/drop"
  },

  // 8. AI 失败模式自检（Lu et al. 2026 Nature）
  "ai_failure_mode_check": {
    "frame_lock": "≤60字：≥1 alternative framing（必）",
    "bug_as_insight": "≤60字 或 N/A",
    "shortcut_risk": "≤60字 或 N/A"
  },

  "papers": [{"title","url","source","published"}]
}
```

**废弃字段**（UI 仍渲染老报告）：`core_claim`（→ formulation）、`score_5d`、`golden_formula`、`falsifying_experiment`、`kill_criterion`、`research_questions`、`study_design`、`prior_art_risk`、`prior_art_check`、`differentiation`、`inspiration`、`connection`、`generation_strategy`

---

## 4. Worked Example：错 vs 对

**主题**：PI 防御范式系统失效

### ❌ 错（claim 重 + 含数值）
```json
"core_claim": "Data-instruction separation 范式系统失效——4 个 defense 在 contextual 类 ASR ≥ 60%"
```
问题：(1) claim 暗示已有证据；(2) 含数值=伪造证据；(3) jargon 满屏；(4) 多句。

### ❌ 半对（plain 但 50+ 字、多句、还有 jargon）
```json
"formulation": "我们假设 data-instruction separation 作为 PI 防御范式在真实部署下系统失效——所有 separation-based defense 在 contextual manipulation 类攻击下均无法有效防御"
```
问题：(1) "——" 把它撕成两句；(2) "separation""contextual manipulation" 是 jargon。

### ✅ 对（one_liner 一句话秒懂）
```json
"idea": {
  "formulation_type": "hypothesis",
  "one_liner": "主流 prompt injection 防御对藏在内容里的指令全都防不住",
  "approach": "选 4 个主流防御（IPI-proxy/WARD/ADR/Sandbox-Guard）× 多种攻击类型；在 LivePI + 自构 unseen-domain corpus 上跑 ASR；按攻击类型分解；用 ANOVA 检验跨防御一致性"
},
"evaluation": {
  "expected_findings": "若假设成立：4 个防御在 contextual 类攻击下 ASR 均 ≥ 60%；跨防御 ASR 方差 < 10pp；防御严格度与 utility 损失 r ≤ -0.7",
  "null_result": "至少 2 个防御在 contextual 类 ASR < 30%；或防御-utility 相关 |r| < 0.3"
}
```

**关键**：one_liner = 27 字、单句、0 jargon（"prompt injection" 是研究对象本身不算）；技术细节全部下沉到 approach 与 evaluation。

---

## 5. 流程（4 步）

### Step 1 — 扫信号
读论文，按 5 类信号扫，每条引用具体论文 + 1 句反常：
失真 / 测量空白 / 承重假设 / 新 affordance / surprise

### Step 2 — 构造 idea
对每条信号写：
1. 选 `strategy`（6 类之一）
2. 选 `formulation_type`（hypothesis / RQ / construct）
3. 写 `formulation`（一句话）+ `approach`
4. 写 `motivation.why_matters` + `signal`
5. 写 `novelty.novelty_type` + `closest_prior_work`（≥1 项）

### Step 3 — 量化 + 评分
1. `evaluation.expected_findings` + `null_result`（具体数字）
2. `feasibility`（data / effort / risks）
3. `finer`（5 维 1-5；avg ≥ 3.0，无单项 < 2）

### Step 4 — Stress Test + 自检
1. `stress_test`（最强反对 + biggest_confound + fallacy_risk）
2. `ai_failure_mode_check.frame_lock`（必）+ bug_as_insight/shortcut_risk（看场景）

---

## 6. 接受门（违一即丢）

### Per-idea
- [ ] **SP Check**（最先）：`starting_point.sp_rating` 填定；`SP_invalid` 立即 cut，不进入后续评分
- [ ] `SP_solid` or `SP_weak` + sp_invalid_reason + operationalizability 已填
- [ ] 5 大字段（idea/motivation/novelty/feasibility/evaluation）+ FINER + stress_test + ai_failure_mode_check 全填
- [ ] `idea.formulation_type / method_type / contribution_form` 三个枚举字段全选定
- [ ] **`idea.one_liner` ≤ 30 字、单句、plain Chinese、禁 jargon、非专家秒懂**（最重要）
- [ ] `one_liner` 主语是现象/失败/假设/问题类/方法（不是工具名）；严禁数值
- [ ] `novelty.closest_prior_work` ≥ 1 项，what_they_did + what_we_dont_do 具体
- [ ] `better_solution` 类 L 与 I 数值都有
- [ ] `evaluation.expected_findings` + `null_result` 都是具体数字
- [ ] `finer.average ≥ 3.0` 且无单项 < 2
- [ ] `stress_test.preprint_risk` 标定；high 必须给降级路径
- [ ] `ai_failure_mode_check.frame_lock` 必填

### Report-level
- [ ] 报告用**单一 `ideas` 列表**（不再分 research_opportunities / idea_sparks——已合并）
- [ ] 至少 1 个 `ecosystem_distortion`
- [ ] 至少 1 个 `phenomenon_discovery / hidden_failure_mode`
- [ ] 至少 50% SE 相关
- [ ] **C1**: `better_solution` 总占比 ≤ 30%
- [ ] **C2**: `better_solution × preprint_risk=high` ≤ 1（或必须 reframe）
- [ ] **C3**: `new_problem` 总占比 ≥ 40%
- [ ] `technical × better_solution` ≤ 20%（旧约束保留）

---

## 7. Concession Threshold（行为协议，appendix）

用户/reviewer pushback 时，**不能因 pushback 单独让步**。打分 1-5：

| 分 | 反驳质量 | 行动 |
|---|---|---|
| 5 | 直击核心 + 新证据/无懈逻辑 | Concede 让步 |
| 4 | 大幅削弱，留小缺口 | Concede 标缺口 |
| 3 | 部分相关但偏离核心 | **Hold** — 重申原 attack |
| 2 | 切边话题 | **Counter** — 指出 deflection |
| 1 | 无证据断言/重复立场 | **Escalate** — 加新角度 |

硬规则：绝不因 pushback 单独让步；不能连续让步（让一条后门槛升 5/5）；单 checkpoint 让步 > 50% → 自查；3 轮 rebuttal 后自问 frame-lock。

日志：`[ANTI-SYCO: Score X/5 | ACTION: ... | REASON: ...]`

---

## 一句话

> **idea 阶段**：先选 formulation_type（hypothesis / RQ / construct），写定性 formulation；数值预测全放 evaluation；用 FINER 评分；reviewer 视角写 stress_test；自查 frame_lock。
