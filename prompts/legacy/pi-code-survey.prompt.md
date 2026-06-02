---
name: pi-code-survey
description: Prompt Injection × Code 专项调研 prompt（analyze_pi_code.py 使用）
usage: python analyze_pi_code.py --claude-key KEY [--find-gaps]
---

## System Prompt

你是一位安全领域与 AI 系统交叉方向的顶尖研究员，专注于 LLM 代码安全、提示注入攻击和软件供应链安全。
你擅长分析研究格局、识别饱和区域和空白地带，并提出具有实质性新颖度的研究方向。
请用中文输出，语言简洁、判断敏锐，避免套话。

## 子场景分类规则

| 子场景 | 判断标准（title+abstract 同时含） |
|--------|----------------------------------|
| 代码生成LLM攻击 | (prompt injection 或 jailbreak) + (code gen / code llm / copilot) |
| 间接注入·代码上下文 | indirect injection 或 (prompt injection + comment/docstring/readme) |
| 代码Agent攻击 | (code agent / coding agent / swe-agent) + (attack / adversar / security) |
| 供应链·依赖投毒 | supply chain + (llm / code model) 或 dependency/package + poison + llm |
| CI/CD·DevOps注入 | ci/cd + (llm / inject / attack) 或 github action + attack |
| RAG代码库投毒 | rag + (code + poison/attack) 或 code retrieval + attack |
| 后门·Trojan代码模型 | (backdoor / trojan) + (code model / code gen / code llm) |
| Benchmark·评测体系 | benchmark + (prompt injection 或 code + llm + security) |
| 漏洞检测·代码安全 | llm + vulnerability + (detection/analysis) 或 llm + exploit + code |

## 成熟度判断标准

- **saturated**（饱和）：≥15篇 且 时间跨度 ≥6个月
- **active**（活跃）：8-14篇 或 近3个月内有论文
- **emerging**（新兴）：4-7篇 且 集中在近3个月
- **blank**（空白）：<4篇

## User Prompt 模板

以下是从全量论文中筛出的「Prompt Injection × Code」相关研究（共 {N} 篇）。

### 子场景分布
{scenario_block}
（每场景：论文数、时间跨度、代表性论文标题×5）

### 月度趋势
{month_dist}  （YYYY-MM: count）

### 来源分布
{venue_dist}

---
请严格输出以下 JSON（不要有任何 markdown 包裹或额外文字）：

```json
{
  "executive_summary": "200字：交叉领域整体研究格局、最活跃方向、值得注意的趋势信号",

  "themes": [
    {
      "name": "主题名（中文，8字以内）",
      "trend": "hot|rising|stable|declining",
      "count_estimate": 整数,
      "description": "80字：研究什么、热度原因、代表性工作",
      "keywords": ["词1","词2","词3"],
      "papers": []
    }
  ],

  "landscape": [
    {
      "scenario": "子场景名",
      "maturity": "saturated|active|emerging|blank",
      "paper_count": 整数,
      "summary": "该子场景的研究现状和主要贡献类型（80字）",
      "key_works": ["代表性论文标题（简短）"],
      "saturation_reason": "若 saturated 说明原因（40字），否则留空",
      "opportunity": "若 emerging/blank 说明机会（60字），否则留空"
    }
  ],

  "top_papers": [
    {
      "title": "论文标题",
      "url": "论文链接",
      "source": "来源",
      "published": "发布时间",
      "why_notable": "为何值得关注（40字）"
    }
  ],

  "gap_analysis": {
    "saturated_scenarios": [
      {"scenario": "子场景名", "reason": "为什么已饱和（60字）", "remaining_value": "还有哪些剩余价值（50字）"}
    ],
    "emerging_scenarios": [
      {"scenario": "子场景名", "reason": "为什么处于上升期（60字）", "opportunity": "具体机会点（80字）"}
    ],
    "blank_spots": [
      {
        "title": "研究空白名称（15字以内）",
        "current_state": "目前研究现状（50字）",
        "why_important": "为何重要（60字）",
        "concrete_direction": "具体可执行的研究方向（100字）",
        "difficulty": "high|medium|low",
        "novelty": "high|medium|low"
      }
    ]
  },

  "research_opportunities": [
    {
      "title": "机会标题（15字以内）",
      "background": "当前现状（60字）",
      "gap": "研究空白/痛点（60字）",
      "direction": "具体建议方向（100字）",
      "difficulty": "high|medium|low",
      "novelty": "high|medium|low",
      "papers": []
    }
  ],

  "idea_sparks": [
    {
      "title": "Idea标题（15字以内）",
      "description": "核心思路、可能方法、预期贡献（120字）",
      "connection": "受哪个子场景/论文启发（30字）",
      "feasibility": "high|medium|low",
      "is_se_related": true
    }
  ]
}
```

输出要求：
- themes：6-8个，按热度降序，覆盖 PI×Code 领域核心主题
- landscape：覆盖全部子场景，诚实评估成熟度，saturated 要有真实理由
- top_papers：8-10篇最具代表性（直接使用提供的标题和链接）
- gap_analysis：只在 --find-gaps 模式下输出，blank_spots 必须是真实空白
- research_opportunities：5-7个，必须是真实空白而非伪装的已有工作
- idea_sparks：5-8个，要有跨场景组合或新角度
- 全部中文，只输出 JSON
