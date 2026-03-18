#!/bin/bash

# Email Insights Agent Setup Script

set -e

echo "🚀 Email Insights Agent Setup"
echo "=============================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python $(python3 --version)"
echo ""

# Check for credentials.json
if [ ! -f "credentials.json" ]; then
    echo "⚠️  credentials.json not found"
    echo ""
    echo "To set up Gmail OAuth:"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a project and enable Gmail API"
    echo "3. Create OAuth 2.0 Client ID (Desktop app)"
    echo "4. Download JSON and save as: credentials.json"
    echo ""
    read -p "Press Enter when credentials.json is ready..."
fi

if [ ! -f "credentials.json" ]; then
    echo "❌ credentials.json still not found"
    exit 1
fi

echo "✅ Found credentials.json"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "✅ Virtual environment ready"
echo ""

# Activate venv
source venv/bin/activate 2>/dev/null || true

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

echo "✅ Dependencies installed"
echo ""

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not set in environment"
    echo ""
    echo "Set it with: export ANTHROPIC_API_KEY=sk-..."
    echo ""
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set ANTHROPIC_API_KEY: export ANTHROPIC_API_KEY=sk-..."
echo "2. Run initial analysis: python main.py initial"
echo "3. Check your email report!"
echo ""
echo "For help: python main.py --help"
