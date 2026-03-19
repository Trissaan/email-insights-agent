# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Email Insights Agent** — An intelligent email analysis system that fetches emails from Gmail, analyzes them using Claude for insights (summaries, categories, sentiment, action items, VIP detection), and generates rich terminal reports.

Three run modes:
1. **Initial**: One-time analysis of last 100 emails (establishes baseline)
2. **Manual**: Force analysis for emails since last run
3. **Daily Cron**: Automated daily analysis at 8:00 AM (configurable)

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Setup: Configure .env with ANTHROPIC_API_KEY
cp .env.example .env
# Edit .env to add your Anthropic API key

# First run (fetches & analyzes last 100 emails)
python main.py initial

# Manual analysis (emails since last run)
python main.py run

# Daily automated runs
python main.py cron

# View saved reports
python main.py report                    # Most recent
python main.py report --date 2026-03-18  # Specific date
```

## Architecture

### Core Modules

| Module | Purpose | Key Responsibilities |
|--------|---------|----------------------|
| **main.py** | CLI entry point | Click-based commands (initial, run, cron, report); validation; report formatting/display |
| **agent.py** | Claude analysis engine | Two-phase email analysis; per-email categorization; aggregate insights generation |
| **gmail_client.py** | Gmail integration | OAuth2 authentication; email fetching; MIME parsing; plain-text extraction |
| **storage.py** | Data persistence | JSON read/write; per-date insights files; last-run timestamp tracking |
| **cron_runner.py** | Daily scheduler | Schedule library integration; daily execution at configured time |
| **config.py** | Configuration | Centralized settings; environment variable loading; directory setup |

### Data Flow

```
User Command
    ↓
[main.py] → CLI validation & dispatch
    ↓
[gmail_client.py] → Fetch emails from INBOX
    ↓
[agent.py] → Phase 1: Analyze each email
             Phase 2: Generate aggregate insights
    ↓
[storage.py] → Save JSON to data/insights/insights_YYYY-MM-DD.json
    ↓
[main.py] → Format & display rich report
```

### Two-Phase Analysis Pattern

**Phase 1: Per-Email Analysis**
- Batches emails (configurable, default 50 per request)
- Claude extracts for each: category, sentiment, priority (1-10), summary, action_items
- Returns structured JSON list

**Phase 2: Aggregate Insights**
- Takes per-email results
- Claude generates: statistics, top action items, VIP senders, health score, trends, recommendations
- Higher-level insights from individual email analysis

This two-phase approach reduces redundant API calls vs. single-phase analysis.

## Key Patterns & Design Decisions

### Configuration via Environment Variables
All key settings live in `config.py` and can be overridden via `.env` or environment variables:
- `ANTHROPIC_API_KEY` — Anthropic API key
- `CLAUDE_MODEL` — Model to use (default: claude-opus-4-6)
- `CRON_HOUR` / `CRON_MINUTE` — Daily run time
- `EMAIL_BATCH_SIZE` — Emails per Claude request
- `MAX_EMAILS_INITIAL` — Initial run email count

### OAuth2 Token Caching
- First run opens browser for Gmail consent (one-time)
- Token saved to `token.json` (auto-refreshed on expiry)
- Subsequent runs use cached token silently
- `credentials.json` (you provide) + `token.json` (auto-generated) are .gitignore'd

### JSON-Based Storage
- Results saved to `data/insights/insights_YYYY-MM-DD.json`
- Per-date files enable trend analysis across multiple runs
- Last-run timestamp in `data/last_run.json`
- Scales to ~1 year of daily data without performance issues

### Error Handling in Agent
- JSON response parsing includes fallback for malformed Claude output
- If JSON parse fails, agent returns basic structure with string representations
- Email parsing is resilient — logs warnings, continues on individual email failures

## Configuration Customization

Edit `config.py` or set environment variables to customize:

```python
# Change daily cron time to 6:00 AM
CRON_HOUR = 6
CRON_MINUTE = 0

# Increase initial analysis from 100 to 200 emails
MAX_EMAILS_INITIAL = 200

# Change batch size for large inboxes
EMAIL_BATCH_SIZE = 100

# Add custom email categories
EMAIL_CATEGORIES = [
    "CRITICAL",
    "CLIENT_REQUEST",
    "INTERNAL",
    "IMPORTANT",
    "ACTION_REQUIRED",
    "NEWSLETTER",
    "SPAM",
    "FOLLOW_UP",
    "FYI",
    "OTHER",
]

# Use a different Claude model
CLAUDE_MODEL = "claude-sonnet-4-6"
```

## File Structure

```
email_agent/
├── main.py                 # CLI: commands and report display
├── agent.py                # Claude analysis (2-phase)
├── gmail_client.py         # Gmail OAuth + API
├── storage.py              # JSON persistence
├── cron_runner.py          # Daily scheduler
├── config.py               # Configuration & paths
├── requirements.txt        # Dependencies
├── .env.example            # Example env file
├── README.md               # Full user documentation
├── QUICKSTART.md           # 5-minute setup guide
├── IMPLEMENTATION_SUMMARY.md # Architecture details
├── credentials.json        # Google Cloud OAuth (you provide, .gitignore'd)
├── token.json              # Gmail OAuth token (auto-generated, .gitignore'd)
└── data/
    ├── last_run.json       # Timestamp of last execution
    └── insights/
        └── insights_YYYY-MM-DD.json  # Per-run analysis results
```

## Important Notes

- **Credentials**: `credentials.json` must be downloaded from Google Cloud Console (OAuth 2.0 Client ID for Desktop application). Never commit this.
- **API Key**: `ANTHROPIC_API_KEY` should be set via `.env` file or environment variable, never hardcoded.
- **Token Refresh**: Gmail tokens auto-refresh; delete `token.json` only if you need to re-authorize with a different account.
- **Batch Processing**: Large email batches are split into configurable chunks (default 50) to respect Claude API limits.
- **Rich Output**: Uses `rich` library for formatted terminal output (tables, colors, panels, progress indicators).

## Testing & Validation

To verify the setup works:
```bash
python test_setup.py  # Validates credentials, API key, dependencies
```

## Common Development Tasks

**Debug email fetching:**
- Check `gmail_client.py:fetch_emails()` for Gmail API query
- Verify OAuth token is fresh (not expired)
- Ensure Gmail API is enabled in Google Cloud Console

**Extend analysis insights:**
- Add new fields to per-email analysis in `agent.py:_analyze_per_email()`
- Add aggregate calculations in `agent.py:_generate_aggregate_insights()`
- Update `main.py:print_report()` to display new fields

**Change email categories or add custom ones:**
- Modify `EMAIL_CATEGORIES` in `config.py`
- Update Claude prompt in `agent.py` to recognize new categories

**Add database instead of JSON:**
- Replace `storage.py` functions with database operations
- Keep the same interface (save_insights, load_insights, etc.)
- Update `config.py` with database connection details

## Dependencies

Key libraries (see `requirements.txt`):
- `anthropic` — Claude API client
- `google-auth-oauthlib`, `google-api-python-client` — Gmail integration
- `click` — CLI framework
- `rich` — Terminal formatting
- `schedule` — Job scheduling
- `python-dotenv` — .env file loading

## Next Steps for New Contributors

1. **Run initial setup**: `python main.py initial` to test end-to-end flow
2. **Review saved JSON**: Check `data/insights/insights_YYYY-MM-DD.json` structure
3. **Read IMPLEMENTATION_SUMMARY.md** for deeper architectural details
4. **Customize in config.py** as needed for your use case
