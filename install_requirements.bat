@echo off
REM install_requirements.bat
REM Installs backend Python dependencies for the project.
REM Usage: install_requirements.bat

cd /d %~dp0\backend
IF EXIST requirements.txt (
    echo Installing Python dependencies from requirements.txt...
    pip install -r requirements.txt
) ELSE (
    echo requirements.txt not found in backend\
    exit /b 1
)
