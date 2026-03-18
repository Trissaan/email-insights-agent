"""Configuration and constants for the email agent."""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INSIGHTS_DIR = DATA_DIR / "insights"
LAST_RUN_FILE = DATA_DIR / "last_run.json"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

# Gmail API
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-opus-4-6"

# Email analysis
EMAIL_BATCH_SIZE = 50  # Chunk size for analysis
MAX_EMAILS_INITIAL = 100

# Cron scheduler
CRON_HOUR = 8
CRON_MINUTE = 0
CRON_SCHEDULE = f"{CRON_MINUTE:02d} {CRON_HOUR:02d}"  # For display

# Email categories
EMAIL_CATEGORIES = [
    "IMPORTANT",
    "ACTION_REQUIRED",
    "NEWSLETTER",
    "SPAM",
    "FOLLOW_UP",
    "FYI",
    "OTHER",
]

# Sentiment types
SENTIMENTS = ["POSITIVE", "NEUTRAL", "NEGATIVE"]

# API limits
MAX_TOKENS_ANALYSIS = 16000
