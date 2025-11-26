#!/bin/bash
# Script to setup Python 3.11 environment and install dependencies

echo "🔧 Setting up GeoChain with Python 3.11"
echo "========================================"

# Check if Python 3.11 is available
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v /opt/homebrew/bin/python3.11 &> /dev/null; then
    PYTHON_CMD="/opt/homebrew/bin/python3.11"
else
    echo "❌ Python 3.11 not found. Installing via Homebrew..."
    brew install python@3.11
    PYTHON_CMD="/opt/homebrew/bin/python3.11"
fi

echo "✅ Using: $PYTHON_CMD"
$PYTHON_CMD --version

# Remove old venv
echo ""
echo "🗑️  Removing old virtual environment..."
rm -rf .venv

# Create new venv with Python 3.11
echo "📦 Creating new virtual environment..."
$PYTHON_CMD -m venv .venv

# Activate and install dependencies
echo "📥 Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Then you can ingest the EPR data:"
echo "  python scripts/ingest_epr.py"