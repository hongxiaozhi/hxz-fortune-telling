#!/bin/bash
# setup.sh - 自动创建并激活Python虚拟环境，并安装依赖
# 兼容Linux/macOS，使用相对路径

set -e

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 虚拟环境目录
VENV_DIR="backend/venv"

# 检查并创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] 创建Python虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

# 激活虚拟环境
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "[ERROR] 未找到虚拟环境激活脚本: $VENV_DIR/bin/activate"
    exit 1
fi

# 升级pip
pip install --upgrade pip

# 安装依赖
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
else
    echo "[WARNING] 未找到requirements.txt，跳过依赖安装"
fi

echo "[INFO] 虚拟环境和依赖安装完成。"
