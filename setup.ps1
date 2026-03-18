# Email Insights Agent Setup Script (PowerShell)

Write-Host "🚀 Email Insights Agent Setup" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green
Write-Host ""

# Check Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

Write-Host "✅ $pythonVersion"
Write-Host ""

# Check for credentials.json
if (-not (Test-Path "credentials.json")) {
    Write-Host "⚠️  credentials.json not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To set up Gmail OAuth:"
    Write-Host "1. Go to https://console.cloud.google.com/"
    Write-Host "2. Create a project and enable Gmail API"
    Write-Host "3. Create OAuth 2.0 Client ID (Desktop app)"
    Write-Host "4. Download JSON and save as: credentials.json"
    Write-Host ""
    Read-Host "Press Enter when credentials.json is ready"
}

if (-not (Test-Path "credentials.json")) {
    Write-Host "❌ credentials.json still not found" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found credentials.json"
Write-Host ""

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..."
    python -m venv venv
}

Write-Host "✅ Virtual environment ready"
Write-Host ""

# Activate venv
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📥 Installing dependencies..."
pip install -q -r requirements.txt

Write-Host "✅ Dependencies installed"
Write-Host ""

# Check API key
if (-not $env:ANTHROPIC_API_KEY) {
    Write-Host "⚠️  ANTHROPIC_API_KEY not set in environment" -ForegroundColor Yellow
    Write-Host ""
    Write-Host 'Set it with: $env:ANTHROPIC_API_KEY = "sk-..."'
    Write-Host ""
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host '1. Set ANTHROPIC_API_KEY: $env:ANTHROPIC_API_KEY = "sk-..."'
Write-Host "2. Run initial analysis: python main.py initial"
Write-Host "3. Check your email report!"
Write-Host ""
Write-Host "For help: python main.py --help"
