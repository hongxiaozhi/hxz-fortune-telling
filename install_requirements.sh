#!/bin/bash
# install_requirements.sh
# Installs backend Python dependencies for the project.
# Usage: bash install_requirements.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

if [ -f requirements.txt ]; then
    echo "Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found in backend/"
    exit 1
fi
