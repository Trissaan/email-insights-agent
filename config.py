"""Configuration and constants for the email agent."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INSIGHTS_DIR = DATA_DIR / "insights"
LAST_RUN_FILE = DATA_DIR / "last_run.json"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

# Gmail API
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-6")

# Email analysis
EMAIL_BATCH_SIZE = int(os.getenv("EMAIL_BATCH_SIZE", "50"))
MAX_EMAILS_INITIAL = int(os.getenv("MAX_EMAILS_INITIAL", "100"))

# Cron scheduler
CRON_HOUR = int(os.getenv("CRON_HOUR", "8"))
CRON_MINUTE = int(os.getenv("CRON_MINUTE", "0"))
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
MAX_TOKENS_CONVERSATION = 1024

# Twilio (WhatsApp/SMS)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")  # e.g., "whatsapp:+14155238886"
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "5000"))
SKIP_TWILIO_VALIDATION = os.getenv("SKIP_TWILIO_VALIDATION", "false").lower() == "true"
ALLOWED_PHONE_NUMBERS = [
    p.strip() for p in os.getenv("ALLOWED_PHONE_NUMBERS", "").split(",") if p.strip()
]

# Conversation history
CONVERSATION_MAX_MESSAGES = int(os.getenv("CONVERSATION_MAX_MESSAGES", "20"))
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"
