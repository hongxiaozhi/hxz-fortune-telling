#!/bin/bash
# upgrade.sh
# Pulls latest code, reinstalls dependencies, and initializes DB if needed.
# Usage: bash upgrade.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Pulling latest code from git..."
git pull

bash install_requirements.sh

if [ -f backend/init_db.py ]; then
    echo "Initializing database..."
    python backend/init_db.py
else
    echo "init_db.py not found in backend/ (skipping DB init)"
fi
