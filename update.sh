#!/bin/bash
# update.sh - Linux/macOS一键拉取更新、升级依赖、初始化数据库并重启后端服务
# 用法：bash update.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 1. 拉取最新代码
echo "[INFO] 拉取最新代码..."
git pull

# 2. 安装/升级依赖和虚拟环境
echo "[INFO] 执行setup.sh升级依赖..."
bash setup.sh

# 3. 初始化数据库（如有）
if [ -f "backend/init_db.py" ]; then
    echo "[INFO] 初始化数据库..."
    source backend/venv/bin/activate
    python backend/init_db.py
else
    echo "[INFO] 未找到init_db.py，跳过数据库初始化"
fi

# 4. 重启后端服务（简单方式：先杀进程再启动）
echo "[INFO] 重启后端服务..."
# 查找并杀死已运行的app.py进程（如有）
PID=$(ps aux | grep '[p]ython.*backend/app.py' | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "[INFO] 杀死旧的后端进程: $PID"
    kill $PID
    sleep 1
fi
source backend/venv/bin/activate
nohup python backend/app.py > backend/server.log 2>&1 &
echo "[INFO] 后端服务已重启，日志见backend/server.log"

# 5. （可选）重启前端服务（如有静态服务器，可补充相关命令）
# echo "[INFO] 重启前端服务..."
# cd frontend && nohup python3 -m http.server 8080 > ../frontend.log 2>&1 &
# echo "[INFO] 前端服务已重启，日志见frontend.log"
