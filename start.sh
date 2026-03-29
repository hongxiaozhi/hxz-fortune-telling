#!/bin/bash
# start.sh
# Starts the backend server for the project.
# Usage: bash start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

if [ -f app.py ]; then
    echo "Starting backend server (app.py)..."
    python3 app.py
else
    echo "app.py not found in backend/"
    exit 1
fi
