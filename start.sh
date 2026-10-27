#!/usr/bin/env bash
# Hyper Video Studio - One-Click Startup Script for macOS / Linux

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================="
echo "🚀 Starting Hyper Video Studio Command Center"
echo "========================================================="

# Ensure npm dependencies are installed
if [ ! -d "node_modules/puppeteer-core" ]; then
    echo "📦 Installing required node dependencies..."
    npm install
fi

# Ensure default sound effects exist
python3 core/sfx_generator.py

# Launch Dashboard
echo "🌟 Dashboard opening on http://localhost:8585"
exec python3 dashboard/server.py
