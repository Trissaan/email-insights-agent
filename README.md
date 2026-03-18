# Email Insights Agent

An intelligent email analysis system powered by Claude that fetches emails from Gmail, analyzes them for insights (summaries, categories, sentiment, action items, VIP senders), and generates rich reports.

## Features

- **Email Analysis**: Categorize emails (IMPORTANT, ACTION_REQUIRED, NEWSLETTER, etc.), detect sentiment, extract action items
- **Inbox Health Score**: Get a 0-10 health assessment of your inbox
- **Smart Summaries**: One-sentence summaries for each email
- **Action Tracking**: Automatic extraction of action items with priority ranking
- **VIP Detection**: Identify high-priority senders and frequent contacts
- **Trend Analysis**: Spot patterns in email volume, sentiment, and categories
- **Three Run Modes**: One-time analysis, manual force-run, or daily automated cron

## Setup

### 1. Prerequisites

- Python 3.8+
- Google Cloud project with Gmail API enabled
- Anthropic API key

### 2. Install Dependencies

```bash
cd email_agent
pip install -r requirements.txt
```

### 3. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Gmail API** (APIs & Services → Enable APIs and Services)
4. Create an **OAuth 2.0 Client ID**:
   - Credentials → Create Credentials → OAuth Client ID
   - Application type: Desktop application
   - Download the JSON credentials file
5. Save the file as `email_agent/credentials.json`

### 4. Set Anthropic API Key

```bash
export ANTHROPIC_API_KEY=sk-...
```

Or on Windows (PowerShell):
```powershell
$env:ANTHROPIC_API_KEY = "sk-..."
```

## Usage

### Initial Analysis (last 100 emails)

Analyze your inbox and establish a baseline:

```bash
python main.py initial
```

This will:
1. Open a browser for Gmail OAuth consent (first run only)
2. Fetch your last 100 emails
3. Analyze them with Claude
4. Display a rich report
5. Save results to `data/insights/insights_YYYY-MM-DD.json`
6. Record the run timestamp

### Force Run (since last analysis)

Run analysis manually at any time for emails received since last run:

```bash
python main.py run
```

Useful for:
- Quick inbox checks during the day
- Manual refreshes outside the scheduled cron time
- Testing after email changes

### Daily Cron Daemon

Start an automated scheduler that runs analysis daily at 8:00 AM (configurable):

```bash
python main.py cron
```

- Runs every day at 08:00 (customize in `config.py`: `CRON_HOUR`, `CRON_MINUTE`)
- Checks every minute for scheduled time
- Fetches only emails since last run (efficient)
- Press Ctrl+C to stop
- Runs in foreground (use `nohup` or supervisor for background)

### View Saved Reports

Display the most recent analysis:

```bash
python main.py report
```

View a specific date:

```bash
python main.py report --date 2026-03-18
```

## Output Format

Each report displays:

```
╔════════════════════════════════════════╗
║   EMAIL INSIGHTS — March 18, 2026      ║
╚════════════════════════════════════════╝

📊 INBOX HEALTH: 7.2/10 | 📧 Analyzed: 100 | 🔥 Action Required: 12 | 👑 VIPs: 5

🔥 TOP ACTION ITEMS
  1. Reply to John about Q1 budget (🔴 HIGH)
  2. Approve project proposal from Sarah (🟡 MID)
  ...

📂 CATEGORIES
  Category          Count  Percentage
  IMPORTANT         32     32.0%
  ACTION_REQUIRED   18     18.0%
  ...

😊 SENTIMENT
  POSITIVE  ████████░░░░░░░░░░ 35 (35.0%)
  NEUTRAL   ████████████░░░░░░ 50 (50.0%)
  ...

👑 VIP SENDERS
  boss@company.com        (12 emails, avg priority 8.5)
  client@example.com      (8 emails, avg priority 7.2)
  ...

📈 KEY TRENDS
  • Email volume increasing on Mondays
  • Sentiment trending positive this week
  ...

💡 RECOMMENDATIONS
  • Consider unsubscribing from low-value newsletters
  • Schedule time to tackle 5+ high-priority items
  ...
```

## Data Storage

```
email_agent/
├── data/
│   ├── last_run.json              # Timestamp of last analysis
│   └── insights/
│       ├── insights_2026-03-18.json
│       ├── insights_2026-03-17.json
│       └── ...
├── token.json                      # Gmail OAuth token (auto-generated)
├── credentials.json                # Google Cloud credentials (you provide)
```

All data is stored locally — nothing is sent to external services except to Claude and Gmail APIs.

## Configuration

Edit `config.py` to customize:

```python
# Cron schedule (24-hour format)
CRON_HOUR = 8        # Run at 8:00 AM
CRON_MINUTE = 0

# Email analysis
MAX_EMAILS_INITIAL = 100      # Emails to fetch on first run
EMAIL_BATCH_SIZE = 50         # Chunk size for large batches

# Claude model
CLAUDE_MODEL = "claude-opus-4-6"
MAX_TOKENS_ANALYSIS = 16000

# Email categories (customize as needed)
EMAIL_CATEGORIES = [
    "IMPORTANT",
    "ACTION_REQUIRED",
    "NEWSLETTER",
    "SPAM",
    "FOLLOW_UP",
    "FYI",
    "OTHER",
]
```

## How It Works

### Phase 1: Email Fetching
- Gmail API retrieves emails from INBOX
- Parses sender, subject, date, and plain-text body
- Handles MIME attachments and multipart messages

### Phase 2: Claude Analysis
- Sends email batch to Claude with analysis instructions
- Claude categorizes each email, assigns sentiment, extracts action items
- Adaptive thinking (`thinking=adaptive`) helps with complex inferences
- Response structured as JSON for reliable parsing

### Phase 3: Aggregate Insights
- Claude generates higher-level insights from per-email analysis
- Identifies VIP senders, trends, recommendations
- Calculates inbox health score

### Phase 4: Storage & Display
- Saves full analysis to JSON for archival
- Updates last-run timestamp
- Displays rich formatted report to terminal

## Troubleshooting

### "Credentials file not found"
- Ensure `credentials.json` is in the `email_agent/` directory
- Download it from Google Cloud Console (see Setup above)

### "ANTHROPIC_API_KEY not set"
- Set the environment variable before running:
  - Linux/Mac: `export ANTHROPIC_API_KEY=sk-...`
  - Windows (PowerShell): `$env:ANTHROPIC_API_KEY = "sk-..."`
  - Windows (CMD): `set ANTHROPIC_API_KEY=sk-...`

### OAuth "invalid_grant" error
- Delete `token.json` and run again — will trigger fresh OAuth consent
- Ensure your Google Cloud credentials are for a Desktop app

### No emails returned
- Check Gmail search syntax in `gmail_client.py`
- Verify the account has emails (not a new or filtered account)

### Claude API rate limit
- Agent automatically batches large runs into 50-email chunks
- Space out manual runs if hitting limits

## File Structure

```
email_agent/
├── main.py                 # CLI entry point (click commands)
├── gmail_client.py         # Gmail API authentication & fetching
├── agent.py                # Claude analysis engine
├── cron_runner.py          # Scheduler (schedule library)
├── storage.py              # JSON persistence
├── config.py               # Configuration & constants
├── __init__.py             # Package marker
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── credentials.json        # Google OAuth (you provide, .gitignore)
├── token.json              # Gmail OAuth token (auto-generated, .gitignore)
└── data/
    ├── last_run.json       # Last execution timestamp
    └── insights/
        └── insights_YYYY-MM-DD.json  # Analysis results per run
```

## Next Steps

1. **Run initial analysis**: `python main.py initial`
2. **Check output**: Rich-formatted report appears in terminal
3. **Set up daily cron**: `python main.py cron` (or use supervisor/systemd)
4. **View trends**: Run `python main.py report` on different days to compare

## Customization Ideas

- Modify email categories in `config.py` to match your workflow
- Adjust `CRON_HOUR` for different run times
- Extend `agent.py` to extract more custom insights (e.g., project tags, urgency signals)
- Add database storage instead of JSON for larger datasets
- Integrate with external systems (e.g., Jira, Slack) to post action items

## License

MIT
