#!/bin/bash
# upgrade.sh
# Pulls latest code, reinstalls dependencies, and initializes DB if needed.
# Usage: bash upgrade.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Pulling latest code from git..."
echo "[INFO] 拉取最新代码..."
git pull

echo "[INFO] 执行setup.sh升级依赖..."
bash setup.sh

if [ -f "backend/init_db.py" ]; then
    echo "[INFO] 初始化数据库..."
    source backend/venv/bin/activate
    python backend/init_db.py
else
    echo "[INFO] 未找到init_db.py，跳过数据库初始化"
fi

echo "[INFO] 升级流程完成。"
