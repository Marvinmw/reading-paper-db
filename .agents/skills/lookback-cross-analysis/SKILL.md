---
name: lookback-cross-analysis
description: 基于过去 N 天/周/月的论文 + 会议论文，做跨时段的深入分析与 cross-paper idea 生成。窗口默认 30 天，可调。触发：「做 lookback 分析」「过去一周/月的论文综述」「cross 一下最近的 idea」「年度会议综述」
---

# Lookback Cross-Time Analysis Skill

## 任务

基于过去 N 天/周/月（或某次会议接收论文）做跨时段分析，目标：
1. 发现 daily 报告漏掉的**跨天主题**
2. 用 cross-paper 信号生成更深入的 idea（不止单 paper 触发）
3. 识别趋势变化 / 论文密度 / 主题热度演化

## 必须先确认（AGENTS.md 协议）

```
准备执行 Lookback Cross-Time Analysis，将使用：

📄 Default：
  - prompts/methodology/idea-generation-method.md（idea 生成方法论）

🛠 Skills 可选启用：
  □ daily-paper-analysis      （需要回看 daily report 时启用）
  □ idea-evaluation           （对 cross idea 做质量门）
  □ pilot-experiment          （对通过 idea 做最小验证）

📋 流程：
  1. 确定窗口（默认 30 天 / 用户可指定 7d / 90d / 某会议）
  2. 聚合 papers + daily reports
  3. 主题 / 趋势分析（密度变化、新词出现率、author overlap）
  4. cross-paper 信号扫描（多 paper 共证一个现象 / 假设破裂）
  5. 生成 cross-idea（按 idea-method 5 大字段）
  6. 保存到 output/reports/report_lookback_YYYYMMDD_HHMM.json

⚙ 默认窗口：30 天（你说「过去一周」→ 7 / 「会议综述」→ 全年）

✅ 确认窗口 + skill 启用？或要调整？
```

## 默认依赖文件

**必读**：
- `prompts/methodology/idea-generation-method.md`

**数据**：
- 窗口内所有 `output/papers/papers_*.json`
- 窗口内所有 `output/reports/report_*.json`（前序 daily report 作为信号源）

## 可选 skills

| Skill | 何时启用 |
|---|---|
| `daily-paper-analysis` | 需要回看 daily report 的 source papers / themes 时 |
| `idea-evaluation` | cross idea 生成后做 FINER + stress test 质量门 |
| `pilot-experiment` | top idea 通过后做 20-50 样本快速验证 |

## 流程详解

### Step 0 — Feedback log + Full-text 准备（强制）

- **Read** `prompts/methodology/idea_feedback_log.md` §2 blacklist
- 筛 top 5 信号 paper 后 WebFetch 完整 PDF，抽 Limitations / Future Work 节

### Step 1 — 确定窗口
默认 30 天。用户可指定：
- `7d` / `30d` / `90d`
- `conf:icse2026` / `conf:ccs2025`（年度会议）
- `since:2026-01-01`（绝对日期）

### Step 2 — 聚合
```python
# pseudo
papers = []
reports = []
for f in glob('output/papers/papers_*.json'):
    if within_window(f, window):
        papers.extend(load(f))
for f in glob('output/reports/report_*.json'):
    if within_window(f, window):
        reports.append(load(f))
# 去重 by url
```

### Step 3 — 主题 / 趋势分析

可做轻量 EDA：
- 时间序列：每周新增 paper 数 / 新词出现率
- 主题分布：themes 在窗口里的密度演化
- 作者 / 机构 overlap：是否出现跨 paper 共同作者
- 关键词演化：新概念 / 老概念退场

### Step 4 — Cross-paper 信号扫描

跨 paper 信号比单 daily 信号更强：
- **多 paper 共证现象** → 强 phenomenon_discovery 信号
- **跨 paper 假设破裂** → 强 assumption_break 信号
- **跨 paper 重复反 pattern** → 强 ecosystem_distortion 信号
- **多 paper 暗示同 failure** → 强 hidden_failure_mode 信号

### Step 5 — 生成 cross-idea

**🚨 Prior-Art 真实搜索硬约束（任何 new_problem 标签前必做）**：
跨时段 lookback 更要做 prior search：corpus 内可能漏掉跨周 / 跨月 preprint。每个 new_problem idea **必须**真去 arxiv + OpenAlex / Semantic Scholar / WebSearch 搜（不只项目内 corpus）。否则 preprint_risk 标签不可信。



每条 cross idea 必须：
- `signal.source_papers` 引用 **≥ 2 篇跨时段论文**（区别于 daily idea 单 paper 触发）
- 按 idea-method 5 大字段完整填
- 在 motivation 里说明「为什么需要 cross-time perspective」

### Step 6 — 保存

```
output/reports/report_lookback_YYYYMMDD_HHMM.json
```

报告 JSON 多两个字段：
- `window`: "30d" / "conf:icse2026" / etc.
- `time_series`: 窗口内的密度演化数据
- `cross_papers_count`: 平均每个 idea 引用的 paper 数

## 用户响应

- 「30 天」/「过去一周」→ 调整窗口
- 「跳过趋势分析」→ Step 3 skip
- 「启用 eval」→ 调用 `idea-evaluation`
