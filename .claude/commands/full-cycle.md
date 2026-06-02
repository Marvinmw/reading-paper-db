---
description: 端到端 4 阶段流水线（爬虫 → daily → 可选 lookback → idea 评估 → digest）。单次确认即放手跑完。
---

# /full-cycle — 4 阶段流水线一键启动

## 参数 (`$ARGUMENTS`)

| 参数 | 含义 | 包含 |
|---|---|---|
| `daily`（默认）| 当日例行 | Step 1 + 2 + 4 + 5 |
| `weekly` | 周复盘 | Step 1 + 2 + 3 (7d) + 4 + 5 |
| `monthly` | 月复盘 | Step 1 + 2 + 3 (30d) + 4 + 5 |
| `conf:<name>` | 会议综述 | Step 1 + 2 + 3 (该会议全集) + 4 + 5 |
| `topic:<topic>` | 主题专项 | Step 1 + 2T (topic-report 替代 daily) + 4 + 5 |

未提供参数 → 默认 `daily`。

**主题模式说明**：`topic:<topic>` 模式下，Step 2 不跑 daily-paper-analysis 而跑 `/topic-report <topic>`（含 Step 2 关键词/子场景确认环节）。Step 3 lookback 自动跳过——topic 本身已是 corpus slice。例：
- `/full-cycle topic:distributed transaction`
- `/full-cycle topic:blockchain smart contract security`
- `/full-cycle topic:DeFi MEV attack`
- `/full-cycle topic:query optimization learned index`

---

## 你是执行引擎。按以下流程跑：

### Step 0 — 单次确认（CLAUDE.md 协议简化版）

**第一次输出必须是**确认模板，等用户回「确认/开始/好/yes」后再动手。任意中断或失败 → 停 + 报错位置，不强推。

确认模板：

```
准备执行 /full-cycle <mode>，将依次跑：

📄 Prompt / Skills（4 项联动）：
  - paper_scraper.py                              （Step 1: 爬论文）
  - .claude/skills/daily-paper-analysis           （Step 2: 当日分析）
    [或 .claude/commands/topic-report.md          （Step 2T 替代: topic:<X> 模式）]
  [- .claude/skills/lookback-cross-analysis       （Step 3: cross-time, 仅 weekly/monthly/conf）]
  - .claude/skills/idea-evaluation                （Step 4: top 3 深度评估）
  - prompts/methodology/digest_template.md        （Step 5: 生成 digest markdown）

🛡 质量门（不可跳过）：
  - prompts/methodology/idea_feedback_log.md §2 blacklist（每次 Step 2/3/4 必读）
  - WebFetch top 5-10 paper full-text Limitations
  - WebSearch prior：每个 new_problem idea 真去 arxiv 搜
  - scripts/validate_idea_report.py（C1/C2/C3 + schema 校验）

📊 Tool 预算（估算）：
  - WebFetch: 5-10 次（top 信号 paper）
  - WebSearch: 12-25 次（prior search + tighter eval search）
  - Bash: ~20 次（脚本 + 校验）
  - 总耗时: 10-20 min depending on corpus size

📁 输出：
  - output/papers/papers_<ts>.json                （Step 1）
  - output/reports/report_<ts>.json               （Step 2）
  [- output/reports/report_lookback_<ts>.json     （Step 3）]
  - output/reports/eval_<ts>.json                 （Step 4，top 3 idea）
  - output/digest_<YYYYMMDD>.md                   （Step 5，人类可读摘要）

🛑 失败处理：
  - 任一步 fail → 停 + 报告失败位置 + 部分产出保留
  - 不破坏性回滚；不重试

✅ 确认开始？或要调整 (如 top N / 跳过某 step)？
```

---

### Step 1 — 跑爬虫

```bash
python3 paper_scraper.py
```

读取最新 `output/papers/papers_*.json`，记录总篇数。

失败 → 停 + 报「Step 1 爬虫失败」。

---

### Step 2 — daily-paper-analysis（daily / weekly / monthly / conf 模式）

按 `.claude/skills/daily-paper-analysis/SKILL.md` 执行（**跳过 SKILL 内的「必须先确认」段**——已在 Step 0 一次性确认）。

执行：
- Step 0 (SKILL 内)：Read `prompts/methodology/idea_feedback_log.md` §2 blacklist
- Step 0.5：WebFetch top 5 paper full-text
- Step 1-5：完整 idea-method 流程
- Step 6：写 JSON 到 `output/reports/report_<ts>.json`

完成后跑 `python3 scripts/validate_idea_report.py output/reports/report_<ts>.json`。

不过 → 停 + 报「Step 2 validator 失败：<violations>」，部分产出留盘。

---

### Step 2T — topic-report（仅 `topic:<topic>` 模式，替代 Step 2）

按 `.claude/commands/topic-report.md` 执行：
- Step 0 (TOPIC 内的确认 + Step 2 关键词/子场景 review) **保留**——这是主题流水唯一的中途用户交互（不在 Step 0 全局确认中 cover，因为主题需要先看到自动提议才能 review）
- Step 3-8：完整流程（filter / full-text / ideas / WebSearch prior / validator / 保存）
- 输出 `output/reports/report_<topic-slug>_<ts>.json`

完成后跑 `python3 scripts/validate_idea_report.py output/reports/report_<topic-slug>_<ts>.json`。

不过 → 停 + 报「Step 2T validator 失败」，部分产出留盘。

**取舍说明**：主题模式不强制 Step 0 一次确认覆盖 Step 2T 的关键词确认——避免「盲跑跑偏主题」。若你想完全免确认，在主题后加 `--skip-confirm`（如 `topic:RAG 安全 --skip-confirm`）。

---

### Step 3 — lookback-cross-analysis（仅 weekly/monthly/conf 模式；topic 模式跳过）

按 `.claude/skills/lookback-cross-analysis/SKILL.md` 执行：
- 窗口：weekly = 7d / monthly = 30d / conf:<name> = 全集
- 同样跳确认（Step 0 已 cover）
- 同样跑 validator

`daily` 和 `topic:<X>` 模式跳过本步。

---

### Step 4 — idea-evaluation（top 3）

加载 Step 2 / 2T（和 Step 3 如有）报告的 `ideas`，按 `finer.average` 降序排前 3。

按 `.claude/skills/idea-evaluation/SKILL.md` 执行：
- §2 blacklist 重对照
- WebSearch tighter prior（含同义词，1-2 query/idea）
- FINER + stress + frame_lock 重审
- Verdict: pass / needs_revision / reject + 具体修订

保存到 `output/reports/eval_<ts>.json`。

若任何 idea 被 reject → prepend `prompts/methodology/idea_feedback_log.md` §3 + 提炼 §2 blacklist。

---

### Step 5 — 生成 daily digest markdown

按 `prompts/methodology/digest_template.md` 的格式，把 Step 1-4 的结果拼成 1 个 markdown 文件保存到 `output/digest_<YYYYMMDD>.md`。

包含：
- 顶部 metadata：日期 / mode / 总耗时 / Tool 调用次数
- Executive summary（200 字）
- Top 5 paper（带 link + 推荐理由）
- 全部 ideas（含 strategy / one_liner / verdict 高亮）
- High-risk idea (preprint_risk=high) 警告段（含 prior collision link + reframe 路径）
- §3 feedback log 本次新增 entry
- Next-step suggestion（按 FINER avg 给 top 3 verdict）

---

### Step 6 — 最终汇报

输出：

```
✅ /full-cycle <mode> 完成
   📁 outputs:
      - papers: papers_<ts>.json (N 篇新增)
      - daily report: report_<ts>.json (M ideas, FINER avg <X.X>)
      [- lookback: report_lookback_<ts>.json]
      - evaluation: eval_<ts>.json (top 3, P passed / Q reject)
      - digest: output/digest_<YYYYMMDD>.md
   📊 stats:
      - Total WebFetch: F
      - Total WebSearch: S
      - Total ideas: M
      - C1/C2/C3 status: PASS / VIOLATED
   🌐 浏览器：http://127.0.0.1:7860「研究报告」标签
   📝 digest 已就绪：output/digest_<YYYYMMDD>.md
```

---

## 注意事项

1. **不要中途问用户**——除了 Step 0 那一次。每步遇到模糊判断，按 SKILL 默认规则走 + 在 digest「Decisions made」段记录。
2. **失败必停**——不要 swallow error。报错位置 + retained outputs 给 user 自己 fix。
3. **Tool 预算超 50 次 WebSearch 时**主动停 + 报告「prior search 异常多，corpus 可能空间饱和」。
4. **idea 数量** Step 2/3 仍按 SKILL 内规则（6-12 idea），Step 4 只 evaluate top 3。
5. **C1/C2/C3 fail** 不强行造数据。停 + 报告原始 candidate pool + 让 user 决定降级或重做。

当前参数: `$ARGUMENTS`
