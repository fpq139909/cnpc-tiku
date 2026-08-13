#!/usr/bin/env bash
# CloudStudio 工作区启动脚本：安装依赖并运行后端
set -e
cd "$(dirname "$0")"
pip install -r requirements.txt -q
echo "GITHUB_TOKEN 已设置: $([ -n "$GITHUB_TOKEN" ] && echo 是 || echo 否)"
exec python cnpc_app.py
