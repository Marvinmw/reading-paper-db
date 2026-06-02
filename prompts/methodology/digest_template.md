---
name: digest_template
description: /full-cycle 末尾生成的人类可读 daily/weekly digest markdown 模板。把 JSON 报告浓缩成 5 分钟可读的简报。
---

# Daily Digest Template

`/full-cycle` 的 Step 5 把所有 JSON 产出按以下模板拼成 `output/digest_<YYYYMMDD>.md`。

## 文件名约定

- 模板：`output/digest_<YYYYMMDD>.md`（每天最多 1 个，多次跑覆盖）
- 若 mode != daily，在文件名后加 mode：`output/digest_20260523_weekly.md`

## 模板正文

```markdown
# 论文调研 Digest — {YYYY-MM-DD} ({mode})

> **Mode**: {daily|weekly|monthly|conf:X}　**Cycle 耗时**: {X} min
> **Tool 调用**: {N} WebFetch + {M} WebSearch + {K} Bash
> **触发命令**: `/full-cycle {mode}`

---

## 0. TL;DR

{2-3 sentence highest-level take-away for the day. e.g. "今日 DeFi oracle 与分布式一致性都有明显信号，2 个 truly new_problem 通过质量门；建议 follow #3 与 #7。"}

---

## 1. Pipeline 状态

| Step | 状态 | 产出 | 耗时 |
|---|---|---|---|
| 1. 爬虫 | ✅/❌ | `papers_<ts>.json` ({N} 新增 / {M} 去重后) | {X} s |
| 2. Daily 分析 | ✅/❌ | `report_<ts>.json` ({P} ideas, FINER avg {X.X}) | {X} min |
| 3. Lookback | ✅/⏭/❌ | `report_lookback_<ts>.json` (cross-paper {P} ideas) | {X} min |
| 4. Idea-eval | ✅/❌ | `eval_<ts>.json` (top 3: {pass} pass / {nr} need rev / {rej} reject) | {X} min |
| 5. Validator | ✅/❌ | C1/C2/C3: {PASS \| VIOLATED} | {s} |

---

## 2. Executive Summary

{从 daily report `executive_summary` 字段抄过来，最多 200 字}

---

## 3. 今日值得读的 5 paper

按 daily report `top_papers` 取前 5：

1. **[{title}]({url})** — {source}, {published}
   {reason 或 why_notable 一句话}
2. ...

---

## 4. Ideas 总览

按 strategy 分类排序展示，每个 idea 一行：

### 4.1 ✅ 通过质量门（{N} 条）

| # | Title | Strategy | FINER | Prior risk | One-liner |
|---|---|---|---|---|---|
| 1 | {title} | {strategy} | {avg} | {preprint_risk} | {one_liner} |
| 2 | ... | ... | ... | ... | ... |

### 4.2 ⚠ 需修订（{N} 条）

| # | Title | 主要问题 | 修订建议 |
|---|---|---|---|
| ... | ... | ... | ... |

### 4.3 ❌ 评估时 reject（{N} 条）

| # | Title | Reject 原因 | Direct prior |
|---|---|---|---|
| ... | ... | ... | [{title}]({url}) |

---

## 5. Top 3 深度评估结果

按 FINER avg 降序，把 `eval_<ts>.json` 的内容展开：

### 5.1 #{rank} {idea_title}

- **Strategy**: {strategy}
- **One-liner**: {one_liner}
- **FINER**: F{f}/I{i}/N{n}/E{e}/R{r} (avg {avg})
- **Verdict**: ✅ pass / ⚠ needs_revision / ❌ reject
- **Verdict 依据**: {verdict_reason}
- **关键 prior**:
  - [{title}]({url}) — {what_they_did} → 我们的差异：{what_we_dont_do}
- **修订/Cut 行动**: {concrete_revisions}

(重复 3 次)

---

## 6. Cross-paper 信号（仅 weekly/monthly/conf mode）

从 lookback report 抽：
- 跨时段密度变化（哪些主题 7d/30d 在涨）
- author/机构 overlap
- 新概念出现率

---

## 7. Feedback Log 本次更新

若 Step 4 reject 了 idea：

### §3 prepend
- **{date}** — {idea_title} collision with [{prior_title}]({prior_url})；教训：{lesson}

### §2 blacklist 新增 pattern (若有)
- {新增 row}

若无 → 写「本次无新增 entry」。

---

## 8. Next-step Suggestion

按 FINER avg 降序，从「✅ 通过」中给：

1. **强推**：第 1 名 + 一句话理由（如「low prior + ecosystem distortion 元层价值高」）
2. **可做**：第 2 名 + 理由
3. **观察**：第 3 名 + 触发条件（如「下周再 search prior 若仍空白则启动」）

---

## 9. Decisions Made（pipeline 中途的默认裁决）

记录 pipeline 跑过程中遇到模糊判断的默认选择，方便事后审计：

- 「top 5 paper 中 2 篇无 HTML render → 只用 abstract anchor」
- 「Step 3 跳过因 daily 模式」
- ...

---

## 10. 文件索引

- 论文：`output/papers/papers_<ts>.json`
- 报告 JSON：`output/reports/report_<ts>.json` [+ `report_lookback_<ts>.json`]
- 评估 JSON：`output/reports/eval_<ts>.json`
- Digest：`output/digest_<YYYYMMDD>.md`
- 浏览器：http://127.0.0.1:7860「研究报告」标签

---

> 🤖 /full-cycle {mode} · Generated {YYYY-MM-DD HH:MM} · Reading Paper Project
```

## 渲染规则

- 数字四舍五入到合适精度（FINER 1 位小数，耗时整数秒）
- 若某 Step skip，对应 §3 / §6 写「跳过 (mode 不含此 Step)」
- §4 表格按 FINER avg 降序
- §5 严格 top 3 from FINER ranking，不超 3 条
- §10 文件路径用相对路径（output/...）

## 写入约定

- 用 Write tool 写到 `output/digest_<YYYYMMDD>.md`
- 若同日已存在 → 加时间戳后缀 `digest_<YYYYMMDD>_<HHMM>.md`，不覆盖
- 多 mode 同日 → mode 加到文件名 `digest_<YYYYMMDD>_<mode>.md`
