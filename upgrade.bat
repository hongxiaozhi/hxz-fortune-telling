@echo off
REM upgrade.bat
REM Pulls latest code, reinstalls dependencies, and initializes DB if needed.
REM Usage: upgrade.bat

cd /d %~dp0

echo Pulling latest code from git...
git pull

call install_requirements.bat

IF EXIST backend\init_db.py (
    echo Initializing database...
    python backend\init_db.py
) ELSE (
    echo init_db.py not found in backend\ (skipping DB init)
)
