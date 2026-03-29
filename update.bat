@echo off
REM update.bat - 一键升级并启动后端服务
REM 用法：update.bat

cd /d %~dp0

REM 1. 拉取最新代码
echo [INFO] 拉取最新代码...
git pull

REM 2. 安装/升级依赖和虚拟环境
echo [INFO] 执行setup.bat升级依赖...
call setup.bat

REM 3. 初始化数据库（如有）
IF EXIST backend\init_db.py (
    echo [INFO] 初始化数据库...
    call backend\venv\Scripts\activate.bat
    python backend\init_db.py
) ELSE (
    echo [INFO] 未找到init_db.py，跳过数据库初始化
)

REM 4. 启动后端服务
echo [INFO] 启动后端服务...
call backend\venv\Scripts\activate.bat
cd backend
python app.py
