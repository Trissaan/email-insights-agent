# Quick Start Guide

Get Email Insights Agent running in 5 minutes.

## 1. Prerequisites

- Python 3.8+
- Google Cloud project with Gmail API enabled
- Anthropic API key (`sk-...`)

## 2. Get Credentials

### Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API (Search for "Gmail API" in the API library)
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
   - Choose "Desktop application"
   - Download the JSON file
5. Save as `email_agent/credentials.json`

### Anthropic API Key

Get your key from [console.anthropic.com](https://console.anthropic.com/api_keys)

## 3. Install

**On Linux/Mac:**
```bash
cd email_agent
chmod +x setup.sh
./setup.sh
```

**On Windows (PowerShell):**
```powershell
cd email_agent
.\setup.ps1
```

**Manual setup:**
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 4. Set Environment Variable

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY=sk-...
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY = "sk-..."
```

**Windows (CMD):**
```cmd
set ANTHROPIC_API_KEY=sk-...
```

## 5. Run

**First time (analyze last 100 emails):**
```bash
python main.py initial
```
→ Browser opens for Gmail OAuth consent (one-time)
→ Fetches and analyzes 100 emails
→ Displays full report

**Check inbox anytime:**
```bash
python main.py run
```
→ Analyzes emails since last run

**Daily automation:**
```bash
python main.py cron
```
→ Runs at 8:00 AM every day (Ctrl+C to stop)

**View past reports:**
```bash
python main.py report
python main.py report --date 2026-03-18
```

## Sample Output

```
╔════════════════════════════════════════╗
║   EMAIL INSIGHTS — March 18, 2026      ║
╚════════════════════════════════════════╝

📊 INBOX HEALTH: 7.2/10 | 📧 Analyzed: 100 | 🔥 Action Required: 12 | 👑 VIPs: 5

🔥 TOP ACTION ITEMS
  1. Reply to John about Q1 budget (🔴 HIGH)
  2. Approve project proposal (🟡 MID)

... [categories, sentiment, VIPs, trends, recommendations] ...
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Credentials file not found" | Save OAuth JSON as `credentials.json` |
| "ANTHROPIC_API_KEY not set" | Set environment variable (see step 4) |
| "invalid_grant" error | Delete `token.json`, run again for fresh OAuth |
| No emails returned | Check inbox exists, try `python main.py --help` |

## Customize

Edit `config.py`:
- `CRON_HOUR`, `CRON_MINUTE` — Change daily run time
- `MAX_EMAILS_INITIAL` — Emails to fetch on first run
- `EMAIL_CATEGORIES` — Custom categories for your workflow

## Next Steps

- Read [README.md](README.md) for full documentation
- Set up daily cron: `python main.py cron`
- Explore saved reports in `data/insights/`
- Customize email categories and cron time in `config.py`
