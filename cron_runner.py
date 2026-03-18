"""Daily scheduler for email analysis."""

import schedule
import time
from datetime import datetime
from typing import Callable

from config import ANTHROPIC_API_KEY, CRON_HOUR, CRON_MINUTE
from gmail_client import GmailClient
from agent import EmailAnalysisAgent
from storage import save_insights, save_last_run, load_last_run


def schedule_daily_run(run_func: Callable, hour: int = CRON_HOUR, minute: int = CRON_MINUTE) -> None:
    """
    Schedule a function to run daily at specified time.

    Args:
        run_func: Function to run
        hour: Hour in 24-hour format (0-23)
        minute: Minute (0-59)
    """
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(run_func)
    print(f"📅 Scheduled daily run at {hour:02d}:{minute:02d}")


def run_daily_analysis() -> None:
    """Run email analysis since last execution."""
    print(f"🔄 Starting daily analysis at {datetime.now()}")

    try:
        # Load last run time
        last_run = load_last_run()

        # Fetch emails
        gmail = GmailClient()
        if last_run:
            print(f"📧 Fetching emails since {last_run}")
            emails = gmail.fetch_emails_since(last_run)
        else:
            print("📧 First run: fetching last 100 emails")
            emails = gmail.fetch_emails(count=100)

        if not emails:
            print("✅ No new emails since last run")
            return

        print(f"📊 Analyzing {len(emails)} emails...")

        # Analyze emails
        agent = EmailAnalysisAgent(ANTHROPIC_API_KEY)
        insights = agent.analyze_emails(emails)

        # Save results
        date_str = datetime.now().strftime("%Y-%m-%d")
        save_insights(insights, date_str)
        save_last_run(datetime.now())

        print(f"✅ Analysis complete! Insights saved for {date_str}")
        print(f"   Health score: {insights['aggregate_insights']['inbox_health_score']:.1f}/10")

    except Exception as e:
        print(f"❌ Daily analysis failed: {e}")


def start_scheduler() -> None:
    """Start the blocking scheduler loop."""
    print("🚀 Email Insights Scheduler started")
    print(f"   Will run daily at {CRON_HOUR:02d}:{CRON_MINUTE:02d}")
    print("   Press Ctrl+C to stop\n")

    schedule_daily_run(run_daily_analysis)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n✅ Scheduler stopped")
