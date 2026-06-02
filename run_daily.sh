#!/usr/bin/env bash
# 每日论文爬取脚本
# 用法：bash run_daily.sh                    使用默认参数
#       bash run_daily.sh --max 30           自定义参数（完全覆盖默认）
#       bash run_daily.sh --keywords "RAG,agent"

set -euo pipefail

# ── 配置 ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="/Users/weima/opt/anaconda3/bin/python"
OUTPUT_DIR="$SCRIPT_DIR/output/papers"
LOG_DIR="$SCRIPT_DIR/logs"

# 如需 Claude 中文摘要，填入 API Key（留空则跳过）
CLAUDE_API_KEY=""

# 命令行参数，默认：DB/Web3/分布式领域过滤 + 每个来源最多 50 篇
ARGS="${*:---max 50 --domain-only}"
if [[ -n "$CLAUDE_API_KEY" ]]; then
    ARGS="$ARGS --claude-key $CLAUDE_API_KEY"
fi

# ── 日志 ──────────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$OUTPUT_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y%m%d).log"
find "$LOG_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null || true

# ── 运行 ──────────────────────────────────────────────────────────────────────
{
echo "========================================"
echo "开始时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "参数：$ARGS"
echo "========================================"

cd "$SCRIPT_DIR"
$PYTHON paper_scraper.py --output "$OUTPUT_DIR" $ARGS

echo ""
echo "结束时间：$(date '+%Y-%m-%d %H:%M:%S')"

# 统计今日输出文件
TODAY=$(date +%Y%m%d)
OUTPUT_FILE=$(ls "$OUTPUT_DIR/papers_${TODAY}"*.md 2>/dev/null | tail -1 || true)
if [[ -n "$OUTPUT_FILE" ]]; then
    COUNT=$(grep -c "^## [0-9]" "$OUTPUT_FILE" 2>/dev/null || echo 0)
    echo "今日论文：$COUNT 篇 → $OUTPUT_FILE"
    # macOS 桌面通知（有桌面环境时生效）
    osascript -e "display notification \"今日爬取 $COUNT 篇论文\" with title \"论文爬取完成\"" 2>/dev/null || true
fi

echo "========================================"
} 2>&1 | tee -a "$LOG_FILE"
