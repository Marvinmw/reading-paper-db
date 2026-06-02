---
name: idea_feedback_log
description: 历次 idea 被拒原因 + 提炼出的模式黑名单。每次生成 idea 前必读 §2 blacklist；每次被用户拒后必更新 §3 history + §2 提取的新 pattern。
---

# Idea Feedback Log（DB / Web3 / 分布式系统领域）

> **强制**：任何生成新 idea 的任务（daily-paper-analysis / lookback / topic-report / idea-evaluation）开始前**必须 Read** 本文档 §2 blacklist，对每个 candidate idea 与 blacklist 对照。匹配项必须 cut 或 explicitly 说明本次为何不同。

---

## §1 工作机制（warning-only 模式）

```
新 idea 候选
  ↓
对照 §2 blacklist
  ↓ 命中 → preprint_risk 提高 + closest_prior_work 写 differentiation
  ↓ 未命中 → preprint_risk 按 WebSearch 实测结果
  ↓
报告生成后 → 用户 review → 反馈（拒/改/接受）
  ↓
若被拒 → §3 加 entry + 提炼到 §2 blacklist
```

**关键原则**：§2 是 risk 标签来源，**不是 cut 决策**。所有 candidate idea 都保留在 report 中，用户读完 differentiation 后自己决定 keep/pivot/drop。

---

## §2 Blacklist：禁止再犯的模式

### B1. 已 saturated 的子领域（先确认这些主题，搜过再说）

| 主题 | 已知 prior（必读后才能 propose 同类）|
|---|---|
| **Raft/Paxos 基础协议 correctness 分析** | 已有大量 TLA+ 验证工作 + Heidi Howard 等系列工作；propose 前必搜 recent 6mo |
| **通用 SQL 查询优化 learned index** | Learned index structures (Kraska et al.) + ALEX + PGM-Index 等已覆盖主流场景 |
| **以太坊 reentrancy 漏洞检测** | Mythril / Slither / Echidna 已覆盖；N+1 工具评测是 better_solution |
| **智能合约 fuzzing** | Echidna / Harvey / ILF 系列；需明确 delta |
| **DeFi 价格 oracle 操纵** | 已有多篇 CCS/S&P 系统研究；需要新 threat model 才是 new_problem |

**铁律**：以上主题任一 → 必须在 propose 前用 WebSearch 搜该子领域最近 6 月 preprint，且自报「我们如何超越/不同于」prior。

### B2. 反 pattern（任意命中即降档 / cut）

| 反 pattern | 例 | 强制动作 |
|---|---|---|
| 加 taxonomy 到已命名现象 | "Flash Loan 攻击加 4-6 类分类" | **不是 new_problem**，必标 better_solution |
| Cross-X 测量已命名现象 | "5 条链 × reentrancy 一致性" | **better_solution** |
| 扩展 X 到新 datastore/chain | "Oracle 操纵从 ETH 扩到 BSC" | **better_solution** |
| N+1 measurement | "他们测 3 种共识，我们测 6 种" | **better_solution** |
| Tool / wrapper | "Slither 增强版 + 1 规则" | 反 pattern；除非 measurable improvement |
| 多 paper synthesis 命名新概念 | "Liquidity Fragmentation Fold" | 风险高——先 search 是否已命名 |

### B3. Methodology 错误（不要再犯）

| 错误 | 防御 |
|---|---|
| 标 new_problem 不先真 search arxiv | §0.65 强制 web search |
| 仅靠 corpus 内 keyword 匹配 ≠ prior search | 必须用 WebSearch 不只 grep 本地 |
| Abstract pattern matching = "灵感" | 必须读 full-text Limitations 节 |
| 把 corpus 当 ground truth | corpus 是 partial snapshot，不是 ground truth |

---

## §3 Rejection History（事故案例库）

按时间倒序。新事故 prepend。

*(目前为空——这是新项目的 clean slate。第一次 idea 被拒后从这里开始记录。)*

---

## §4 维护

- 用户每次拒 idea → 我 prepend §3 + 更新 §2 提取的 pattern
- 每周 review §2 blacklist 看是否过时（如有新 paper 反驳某 prior）
- 本文档**不要删任何 entry**——历史记录是模式提炼的依据
