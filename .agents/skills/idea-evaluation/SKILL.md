---
name: idea-evaluation
description: 对单条或一组 idea 做严格质量评估——FINER 五维 + stress_test（Devil's Advocate）+ AI 失败模式自检 + prior-art 检查 + Concession Threshold。可独立调用，也可作为 daily/lookback skill 的质量门。触发：「评估这条 idea」「这个 idea 质量怎样」「这条 idea 能投顶会吗」「升级这个 idea」
---

# Idea Evaluation Skill

## 任务

对已有 idea（来自 daily report、lookback report、或用户手写）应用严格质量评估并产出评估报告。**独立 skill，可在任何阶段调用**。

## 必须先确认（AGENTS.md 协议）

```
准备执行 Idea Evaluation，将使用：

📄 Default：
  - prompts/methodology/idea-generation-method.md（评估标准定义）

🛠 Skills 可选启用：
  □ daily-paper-analysis      （回到 report 上下文查看 source papers）
  □ lookback-cross-analysis   （需要跨时段证据时启用）
  □ pilot-experiment          （对通过 idea 设计最小验证）

📋 流程：
  0. Starting Point Validity（**最先**）：SP-1 主干性 + SP-2 可操作性 + SP-3 作者态度；SP_invalid → 直接 cut，不跑后续
  1. 加载 idea（指定文件 / 报告中第 N 条 / 用户手写）
  2. FINER 五维评分（avg ≥ 3.0 + 单项 ≥ 2）
  3. Stress test（strongest_counter + biggest_confound + fallacy_risk）
  4. AI 失败模式自检（frame_lock 必，bug_as_insight / shortcut_risk 看场景）
  5. Prior-art 检查（本地 grep + arxiv / OpenAlex / Semantic Scholar / WebSearch 真搜）
  6. 综合判断：通过 / 需修(warning) / 退档（仅结构性失败，prior collision 不退档）
  7. 产出 evaluation 报告（追加到原 idea 或独立文件）

✅ 确认 + 指定 idea 来源（文件路径 / 报告条目）？
```

## 默认依赖文件

**必读**：
- `prompts/methodology/idea-generation-method.md` §3-§7（评分 / stress / 失败模式 / Concession 协议）

**输入**：
- 一条 idea（JSON 片段）或一组 idea（来自某报告）
- 用户可指定 `output/reports/<file>.json` 的 `ideas[N]`

## 可选 skills

| Skill | 何时启用 |
|---|---|
| `lookback-cross-analysis` | 需要跨天 / 跨会议证据判断 novelty 时 |
| `pilot-experiment` | idea 通过后，想马上验证核心信号时 |
| `daily-paper-analysis` | 需要回看原 daily report 的 source paper context 时 |

## 评估维度（必跑）

### 0. Starting Point Validity（**最先，SP_invalid = 直接 cut**）

三问检查（见 `idea-generation-method.md §0.6`）：

| 检查 | 关键判断 |
|---|---|
| **SP-1 主干性** | 起点来自 source paper 的 main finding，还是 Limitations / footnote？|
| **SP-2 可操作性** | 核心 phenomenon 能不循环地定义 + 测量吗？|
| **SP-3 作者态度** | 原作者是否已放弃该方向（"resists quantification" 等）？|

- 全部通过 → `SP_solid`，继续评估
- 1-2 项弱但有改进路径 → `SP_weak`，标注后继续（FINER Feasible 上限 3）
- 任一致命失败（footnote + 作者放弃 + 无可操作方案）→ `SP_invalid`，**立即 cut，跳过后续所有维度**，直接出 verdict = reject + sp_cut_reason

**SP_invalid cut 时必做**：
1. 写 sp_cut_reason（≤60字，引用三问哪条失败）
2. prepend §3 到 `prompts/methodology/idea_feedback_log.md`（记录具体 cut 原因）
3. 检查是否触发新 §2 blacklist 模式

---

### 1. FINER 五维（avg ≥ 3.0 且无单项 < 2）
| 维度 | 标准 |
|---|---|
| Feasible | 数据可得 + 方法明确 |
| Interesting | 解决真悖论 vs 已知琐碎 |
| Novel | 新视角 / 方法 / 证据 |
| Ethical | 风险 vs 收益 |
| Relevant | 改变 policy / practice / theory |

### 2. Stress Test
- `strongest_counter`：reviewer 最强反驳（≤80 字）
- `biggest_confound`：最大替代解释（≤80 字）
- `fallacy_risk`：6 类之一（confirmation_bias / hasty_generalization / cherry_picking / survivorship_bias / ecological_fallacy / none）

### 3. AI 失败模式自检（Lu et al. 2026 Nature）
- `frame_lock`：≥1 alternative framing（必填）
- `bug_as_insight`：surprise 类 signal 必查
- `shortcut_risk`：empirical idea 必查

### 0a. Feedback log 必读

**Read** `prompts/methodology/idea_feedback_log.md` §2 blacklist。candidate idea 任意匹配 blacklist → verdict = reject 或 explicit 说明本次为何不同。

### 4. Prior-art 检查（**强制真实 search，warning-only 不 cut**）

- 抓 idea title + one_liner 关键词 + 同义词组
- **必须**跑 arxiv + OpenAlex / Semantic Scholar / WebSearch 中至少两类来源（不只本地 corpus）
- 仅 grep 本地 corpus 是**结构性盲点**：项目内可能漏掉 arxiv 同月新 preprint
- HARD collision (≥1 篇 same-month direct prior) → `preprint_risk=high` + closest_prior_work 必写 differentiation + preprint_risk_reason 含 reframe 路径
- MEDIUM / LOW → 对应 risk 等级
- **不自动降档 better_solution，不自动 cut**——把所有 collision 信息透明展示，让用户决策

**事故案例**（2026-05-23）：CI/CD AWI idea 标 new_problem + preprint_risk=low，但 Wang et al. arXiv 2605.07135 直接覆盖 — corpus 内未爬到该 paper，仅靠本地匹配漏检。**真实 search 是 idea_evaluation 的入门条件**。

### 5. one_liner 质量检查
- ≤ 30 字（宽容 35）
- 单句
- 禁 jargon（黑名单见 idea-method §0.5）
- 非专家秒懂

### 6. 数值分布检查
- core_claim / one_liner / approach 严禁数值
- 数值必须在 evaluation.expected_findings + null_result

## 综合判断（**warning-first, 仅严重结构问题才 reject**）

| 状态 | 触发条件 | 行动 |
|---|---|---|
| ✂ **SP Cut** | `starting_point.sp_rating = SP_invalid`（三问任一致命失败）| **最先判定，跳过后续所有维度**；verdict = reject；prepend §3 + 检查 §2 新 pattern |
| ✅ **通过** | SP 通过 + FINER ≥ 4.0 + 所有维度通过 | 入库 |
| ⚠ **需修 (差异化警告)** | SP_weak / FINER 3.0-4.0 / prior HARD collision（不论是否 reframe）/ 撞 §2 blacklist | 标 preprint_risk=high + 必写 differentiation + reframe 退路 + **保留 idea 给用户决策** |
| ❌ **退档** | FINER avg < 3.0 或单项 < 2 / one_liner 结构违规 / schema 缺失字段 | 真不可挽救才 reject——不能因「有 prior」就 reject |

**关键原则**：
- SP Check 是硬性 gate，**先于 FINER**，SP_invalid = no questions asked, cut
- Prior collision 不是 reject 理由，是 risk 标签。用户看完 differentiation 后自己决定

## Post-evaluation 反馈

evaluation 结束后，若 verdict = reject 或 needs_revision：
- 把 idea title + reject reason + 关键 prior 论文 prepend 到 `prompts/methodology/idea_feedback_log.md` §3
- 若发现新模式（如「某类 framing 反复被拒」）→ 加到 §2 blacklist
- 用户每次拒 idea 就是 negative training，**必须固化**否则白拒

## Concession Threshold 行为

评估时若用户对评估结论 pushback，按 idea-generation-method §7 协议：
- 打 1-5 分对方反驳质量
- < 4 分不让步 → Hold / Counter / Escalate
- 每次决策日志化 `[ANTI-SYCO: ...]`

## 产出格式

```json
{
  "idea_title": "...",
  "evaluation": {
    "starting_point_check": {
      "sp_rating": "SP_solid | SP_weak | SP_invalid",
      "sp1_source_type": "main_finding | secondary_finding | limitation | footnote | user_observation",
      "sp2_operationalizability": "通过 | 失败: <原因>",
      "sp3_author_stance": "pursuing | neutral | abandoned",
      "sp_cut_reason": "（仅 SP_invalid 填）≤60字"
    },
    "finer": {...},
    "stress_test": {...},
    "ai_failure_mode_check": {...},
    "prior_art_check": {...},
    "one_liner_check": {"length": N, "single_sentence": true, "jargon_free": true},
    "numeric_separation_check": "OK | violations: [...]",
    "verdict": "sp_cut | pass | needs_revision | reject",
    "verdict_reason": "...",
    "concrete_revisions": ["...", "..."]
  }
}
```

可独立保存，或 patch 回原 idea。

## 用户响应

- 「评估 report_X.json 的第 3 条」→ 加载并跑
- 「评估这条 [手写 idea]」→ 接收 JSON 片段
- 「全部 idea」→ 跑整个 report 所有 idea
- 「启用 lit-search 核查 novelty」→ 做 arxiv + OpenAlex / Semantic Scholar / WebSearch prior-art search
