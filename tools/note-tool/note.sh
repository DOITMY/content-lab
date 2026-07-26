#!/usr/bin/env bash
# 笔记提取工具 - 快捷运行脚本
# 从 ~/.hermes/.env 读取 DeepSeek API 密钥
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 从 Hermes 环境变量读取
if [ -f "$HOME/.hermes/.env" ]; then
    # shellcheck disable=SC1090
    source <(grep -E "^(DEEPSEEK_API_KEY|DEEPSEEK_BASE_URL|GETNOTE_API_KEY|GETNOTE_CLIENT_ID)=" "$HOME/.hermes/.env")
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  未设置 DEEPSEEK_API_KEY，将使用本地格式化（无 AI 仿写）"
    echo "   可在 ~/.hermes/.env 中设置："
    echo "   echo 'DEEPSEEK_API_KEY=sk-your-key' >> ~/.hermes/.env"
fi

exec python3 "$SCRIPT_DIR/note_tool.py" "$@"
