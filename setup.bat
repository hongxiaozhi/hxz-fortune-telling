@echo off
REM setup.bat - 自动创建并激活Python虚拟环境，并安装依赖
REM 用法：setup.bat

cd /d %~dp0

REM 虚拟环境目录
SET VENV_DIR=backend\venv

REM 检查并创建虚拟环境
IF NOT EXIST %VENV_DIR% (
    echo [INFO] 创建Python虚拟环境...
    python -m venv %VENV_DIR%
)

REM 激活虚拟环境
IF EXIST %VENV_DIR%\Scripts\activate.bat (
    call %VENV_DIR%\Scripts\activate.bat
) ELSE (
    echo [ERROR] 未找到虚拟环境激活脚本: %VENV_DIR%\Scripts\activate.bat
    exit /b 1
)

REM 升级pip
python -m pip install --upgrade pip

REM 安装依赖
IF EXIST backend\requirements.txt (
    pip install -r backend\requirements.txt
) ELSE (
    echo [WARNING] 未找到requirements.txt，跳过依赖安装
)

echo [INFO] 虚拟环境和依赖安装完成。
