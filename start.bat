@echo off
REM start.bat
REM Starts the backend server for the project.
REM Usage: start.bat

cd /d %~dp0\backend
IF EXIST app.py (
    echo Starting backend server (app.py)...
    python3 app.py
) ELSE (
    echo app.py not found in backend\
    exit /b 1
)
