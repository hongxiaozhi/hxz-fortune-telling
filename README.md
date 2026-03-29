
# HXZ Fortune Project — Cross-Platform Script Guide

This project provides a set of cross-platform scripts for setup, development, and maintenance. All scripts are located in the project root and are available in both Windows (`.bat`) and Unix-like (`.sh`) formats.

---

## Prerequisites

- **Python 3.7+** and **pip** must be installed and available in your system PATH.
- **Git** is required for upgrade scripts.
- For Unix-like systems (Linux/macOS):
  - You may need to grant execute permission: `chmod +x *.sh`
- For Windows: Scripts can be double-clicked or run from Command Prompt/PowerShell.

---

## Script Overview

| Script                      | Purpose                                                      |
|-----------------------------|--------------------------------------------------------------|
| setup.sh                    | Create/activate venv and install backend Python dependencies |
| start.sh/.bat               | Start the backend server (`backend/app.py`)                  |
| upgrade.sh/.bat             | Pull latest code, reinstall dependencies, init database      |

---

## 1. 环境初始化与依赖安装

推荐使用 `setup.sh`（Linux/macOS/WSL）或 `setup.bat`（Windows）自动创建/激活虚拟环境并安装依赖。

**Linux/macOS/WSL:**

  bash setup.sh

**Windows:**

  setup.bat

---

## 2. Starting the Backend Server

Launches the backend Flask server (`backend/app.py`).

**Windows:**

    start.bat

**Linux/macOS:**

    bash start.sh

---

## 3. Upgrading the Project

Pulls the latest code from git, reinstalls dependencies, and initializes the database if `backend/init_db.py` exists.

**Windows:**

    upgrade.bat

**Linux/macOS:**

    bash upgrade.sh

---

## Usage Examples

### Windows (Command Prompt or PowerShell)

    setup.bat
    start.bat
    upgrade.bat

### Unix-like (Linux/macOS Terminal)

    chmod +x *.sh  # (first time only, if needed)
    bash setup.sh
    bash start.sh
    bash upgrade.sh

---

## Troubleshooting

- **Python or pip not found:**
  - Ensure Python and pip are installed and added to your system PATH.
- **Permission denied (Unix):**
  - Run `chmod +x *.sh` to make scripts executable.
- **requirements.txt or app.py not found:**
  - Make sure you are running scripts from the project root directory.
- **Git errors during upgrade:**
  - Ensure git is installed and you have network access.
- **Database not initialized:**
  - Check that `backend/init_db.py` exists and is error-free.
- **Other errors:**
  - Review the script output and comments for hints. Most scripts exit with a message if a required file is missing.

---

## Additional Notes

- Scripts use relative paths and must be run from the project root.
- For custom environments, you may edit the scripts as needed.
- For further help, consult script comments or contact the project maintainer.
