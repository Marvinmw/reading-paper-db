---
description: 以 prompt 作为程序执行分析任务，不调用外部 LLM API
---

# Prompt-as-Program 模式

**你是执行引擎。当任务需要 LLM 分析时，不写调用 API 的代码，而是把 prompt 当作程序，自己加载执行。**

## 触发条件

当任务满足以下任意一条时，自动进入此模式：

- 需要分析、总结、分类大量文本（论文、代码、日志等）
- 需要生成结构化报告（JSON / Markdown）
- 原有脚本里有 `anthropic.Anthropic().messages.create(...)` 调用
- 用户说「生成报告」「分析这些」「总结一下」

## 执行流程

### Step 1 — 写 prompt 文件

在 `prompts/` 目录下创建 `<任务名>.prompt.md`，包含：

```markdown
---
name: <任务名>
description: <一句话说明>
---

## System Role
<你扮演什么角色，有什么专长>

## 输入格式
<描述输入数据的结构>

## 分析指令
<具体要做什么，步骤清单>

## 输出 Schema
<期望的 JSON 或 Markdown 结构>
```

### Step 2 — 加载输入数据

用工具（Read / Bash）读取实际数据：论文 JSON、代码文件、日志等。

### Step 3 — 执行分析

按照 prompt 文件里的指令，**自己完成分析**：
- 阅读每条输入
- 按 System Role 的视角思考
- 生成符合 Output Schema 的结构化结果

### Step 4 — 保存输出

用 Write 工具把结果保存到目标文件。

---

## 禁止行为

- ❌ 不写 `import anthropic` 或 `openai`
- ❌ 不写 `client.messages.create(...)`
- ❌ 不建议用户「填入 API Key」再运行脚本

## 允许行为

- ✅ 自己读数据、自己分析、自己写结果
- ✅ 在 prompts/ 留下可复用的 prompt 文件
- ✅ 如果分析量极大（>500条），先抽样统计再全量归纳
