# Prompts — 项目工作流索引

按角色组织：
```
prompts/
├── methodology/     ← 跨任务共用的方法论文档
├── commands/        ← slash command 入口（人读 + LLM 执行）
└── legacy/          ← 老 API prompt templates（归档）
```

---

## 任务 → Skill → Prompt 文件 映射

每个常见任务有专属 `.agents/skills/<name>/SKILL.md`，里面已自带「必须先确认」段和详细清单。下面是快速索引。

### 一键全流程: `/full-cycle [daily|weekly|monthly|conf:X]`
- **Slash command**: `AGENTS.md` 中定义的 `/full-cycle`
- **串联**: Step 1 (爬虫) + Step 2 (daily) + [Step 3 lookback if weekly+] + Step 4 (idea-eval top 3) + Step 5 (digest)
- **必读 prompts**:
  - `methodology/idea-generation-method.md` — idea 5 大字段
  - `methodology/idea_feedback_log.md` — §2 blacklist（每步必读）
  - `methodology/digest_template.md` — Step 5 markdown 输出格式
- **质量门保留**: §2 blacklist + WebSearch prior + Validator C1/C2/C3
- **触发**：「/full-cycle」「跑今天全流程」「自动跑一遍周复盘」
- **详见**: 主 README「一键全流程」段

### Step 2: 分析当日论文 / 生成 daily report
- **Skill**: `daily-paper-analysis`（见 `.agents/skills/daily-paper-analysis/SKILL.md`）
- **必读 prompts**:
  - `commands/daily_report.md` — 报告大纲 + JSON schema
  - `methodology/idea-generation-method.md` — idea 5 大字段
- **可选 skills**: `idea-evaluation` / `pilot-experiment`
- **触发**：「生成 daily report」「分析今日论文」

### Step 3: 跨时段分析 / lookback
- **Skill**: `lookback-cross-analysis`（见 `.agents/skills/lookback-cross-analysis/SKILL.md`）
- **必读 prompts**: `methodology/idea-generation-method.md`
- **可选 skills**: `daily-paper-analysis` / `idea-evaluation` / `pilot-experiment`
- **触发**：「过去一周/月分析」「会议论文综述」「cross-paper idea」

### Step 4: idea 评估 / 质量门
- **Skill**: `idea-evaluation`（见 `.agents/skills/idea-evaluation/SKILL.md`）
- **必读 prompts**: `methodology/idea-generation-method.md` §3-§7
- **可选 skills**: `lookback-cross-analysis` / `pilot-experiment`
- **触发**：「评估这条 idea」「这 idea 质量怎样」「升级这个 idea」

### 主题专项调研（通用）
- **Slash command**: `AGENTS.md` 中定义的 `/topic-report <topic>`
- **必读**: `methodology/idea-generation-method.md` + `methodology/idea_feedback_log.md` §2
- **触发**：「/topic-report <主题>」「调研 <主题>」「<主题> 专项报告」
- **Step 2 关键交互**: Claude 自动提关键词 + 子场景 → 你 review 调整
- **主题示例**：distributed transaction / smart contract security / DeFi MEV / query optimization / consensus fault tolerance

### Prompt-as-Program 规范
- **Slash command**: `prompts/commands/prompt-as-program.md`
- 任何分析任务都不写 anthropic.client.create()——自己 Read 数据自己分析

---

## 文件清单

### methodology/
| 文件 | 作用 |
|---|---|
| `idea-generation-method.md` | idea 5 大字段（idea/motivation/novelty/feasibility/evaluation）+ FINER 评分 + stress_test + AI 失败模式自检 + Concession Threshold |
| `idea_feedback_log.md` | §2 blacklist 饱和子领域 + §3 rejection history（每次 idea 生成必读）|
| `digest_template.md` | `/full-cycle` Step 5 markdown digest 输出模板 |

### commands/
| 文件 | 作用 | 触发 |
|---|---|---|
| `daily_report.md` | daily 报告 schema + 流程 | 「生成 daily report」|
| `prompt-as-program.md` | 不调外部 LLM API 的执行规范 | 任何分析任务自动遵守 |

> **注**：`/full-cycle` 与 `/topic-report` 的项目协议集中写在 `AGENTS.md`，prompt 文件只保存可复用执行规范。


### legacy/（归档不删）
| 文件 | 历史用途 |
|---|---|
| `daily-report.prompt.md` | 旧 generate_report.py 用的 API prompt |
| `pi-code-survey.prompt.md` | 旧 SE/PI×Code 项目 API prompt，保留作迁移参考 |
| `similar-idea-search.prompt.md` | 旧 idea 相似性搜索 prompt |

---

## 与 playbook/ 的关系

- **prompts/** = 本项目执行机器（active workflow）
- `methodology/idea-generation-method.md` 借鉴了 FINER / Devil's Advocate / abductive iteration 等通用方法，但是 standalone，不依赖外部 playbook 文件即可工作。

---

## 行为协议（来自 AGENTS.md）

执行任何上面任务前**先输出确认清单**（哪些 skill / prompt + 流程概要 + 等用户确认）。每个项目 SKILL.md 内已含模板，直接 Read 后输出即可。
