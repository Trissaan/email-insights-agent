"""CLI for email insights agent."""

import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import ANTHROPIC_API_KEY, CRON_HOUR, CRON_MINUTE
from gmail_client import GmailClient
from agent import EmailAnalysisAgent
from storage import save_insights, save_last_run, load_last_run, get_most_recent_insights
from cron_runner import start_scheduler, run_daily_analysis

console = Console()


def validate_setup() -> None:
    """Validate that required credentials exist."""
    from config import CREDENTIALS_FILE

    if not CREDENTIALS_FILE.exists():
        console.print(
            f"❌ [red]Credentials file not found[/red]\n"
            f"   Please download OAuth credentials from Google Cloud Console\n"
            f"   Save to: {CREDENTIALS_FILE}",
            style="bold red",
        )
        sys.exit(1)

    if not ANTHROPIC_API_KEY:
        console.print(
            "❌ [red]ANTHROPIC_API_KEY not set[/red]\n"
            "   Set via: export ANTHROPIC_API_KEY=sk-...",
            style="bold red",
        )
        sys.exit(1)


def print_report(insights: dict, title: str = "EMAIL INSIGHTS") -> None:
    """Print formatted insights report."""
    agg = insights.get("aggregate_insights", {})

    # Header
    console.print(
        Panel(
            f"[bold cyan]{title}[/bold cyan] — {datetime.now().strftime('%B %d, %Y')}",
            expand=False,
        )
    )

    # Health score and counts
    health = agg.get("inbox_health_score", 0)
    email_count = insights.get("email_count", 0)
    action_required = agg.get("category_breakdown", {}).get("ACTION_REQUIRED", 0)
    vip_count = len(agg.get("vip_senders", []))

    health_color = "green" if health >= 7 else "yellow" if health >= 5 else "red"
    console.print(
        f"📊 [bold]INBOX HEALTH[/bold]: "
        f"[{health_color}]{health:.1f}/10[/{health_color}] | "
        f"📧 Analyzed: {email_count} | "
        f"🔥 Action Required: {action_required} | "
        f"👑 VIPs: {vip_count}\n"
    )

    # Top action items
    action_items = agg.get("top_action_items", [])
    if action_items:
        console.print("[bold]🔥 TOP ACTION ITEMS[/bold]")
        for i, item in enumerate(action_items, 1):
            priority = item.get("priority", 5)
            priority_str = "🔴 HIGH" if priority >= 8 else "🟡 MID" if priority >= 5 else "🟢 LOW"
            console.print(
                f"  {i}. {item['item'][:60]} ({priority_str})\n"
                f"     From: {item['from']}"
            )
        console.print()

    # Category breakdown
    categories = agg.get("category_breakdown", {})
    if categories:
        console.print("[bold]📂 CATEGORIES[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Category")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        total = sum(categories.values())
        for cat in sorted(categories.keys()):
            count = categories[cat]
            pct = (count / total * 100) if total > 0 else 0
            table.add_row(cat, str(count), f"{pct:.1f}%")

        console.print(table)
        console.print()

    # Sentiment breakdown
    sentiments = agg.get("sentiment_breakdown", {})
    if sentiments:
        console.print("[bold]😊 SENTIMENT[/bold]")
        for sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
            count = sentiments.get(sentiment, 0)
            pct = (count / email_count * 100) if email_count > 0 else 0
            bar_length = int(pct / 2)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            console.print(f"  {sentiment:10} {bar} {count} ({pct:.1f}%)")
        console.print()

    # VIP senders
    vips = agg.get("vip_senders", [])
    if vips:
        console.print("[bold]👑 VIP SENDERS[/bold]")
        for sender in vips:
            count = sender.get("email_count", 0)
            priority = sender.get("avg_priority", 0)
            console.print(
                f"  {sender['sender'][:40]:40} ({count} emails, avg priority {priority:.1f})"
            )
        console.print()

    # Trends and recommendations
    trends = agg.get("key_trends", [])
    if trends:
        console.print("[bold]📈 KEY TRENDS[/bold]")
        for trend in trends:
            console.print(f"  • {trend}")
        console.print()

    recommendations = agg.get("recommendations", [])
    if recommendations:
        console.print("[bold]💡 RECOMMENDATIONS[/bold]")
        for rec in recommendations:
            console.print(f"  • {rec}")


@click.group()
def cli():
    """Email Insights Agent — Analyze your inbox with Claude."""
    pass


@cli.command()
def initial():
    """Analyze last 100 emails (one-time)."""
    validate_setup()

    console.print("🚀 [bold]Running initial analysis[/bold]\n")

    try:
        # Fetch emails
        console.print("📧 Fetching last 100 emails...")
        gmail = GmailClient()
        emails = gmail.fetch_emails(count=100)

        if not emails:
            console.print("❌ No emails found in inbox")
            return

        console.print(f"✅ Fetched {len(emails)} emails\n")

        # Analyze
        console.print(f"🧠 Analyzing emails with Claude...")
        agent = EmailAnalysisAgent(ANTHROPIC_API_KEY)
        insights = agent.analyze_emails(emails)

        # Save
        date_str = datetime.now().strftime("%Y-%m-%d")
        save_insights(insights, date_str)
        save_last_run(datetime.now())

        console.print("✅ Analysis saved\n")

        # Display report
        print_report(insights, "EMAIL INSIGHTS — INITIAL RUN")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1)


@cli.command()
def run():
    """Force run now (emails since last run)."""
    validate_setup()

    console.print("🚀 [bold]Running forced analysis[/bold]\n")

    try:
        # Determine start point
        last_run = load_last_run()
        if last_run:
            console.print(f"📧 Fetching emails since {last_run.strftime('%Y-%m-%d %H:%M')}")
        else:
            console.print("📧 First run: fetching last 100 emails")

        gmail = GmailClient()
        if last_run:
            emails = gmail.fetch_emails_since(last_run)
        else:
            emails = gmail.fetch_emails(count=100)

        if not emails:
            console.print("✅ No new emails since last run")
            return

        console.print(f"✅ Fetched {len(emails)} emails\n")

        # Analyze
        console.print("🧠 Analyzing emails with Claude...")
        agent = EmailAnalysisAgent(ANTHROPIC_API_KEY)
        insights = agent.analyze_emails(emails)

        # Save
        date_str = datetime.now().strftime("%Y-%m-%d")
        save_insights(insights, date_str)
        save_last_run(datetime.now())

        console.print("✅ Analysis saved\n")

        # Display report
        print_report(insights)

    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1)


@cli.command()
def cron():
    """Start daily cron daemon (blocking)."""
    validate_setup()
    start_scheduler()


@cli.command()
@click.option("--port", default=None, type=int, help="Port to run webhook server (default: 5000)")
@click.option("--debug", is_flag=True, default=False, help="Enable debug mode")
def serve(port, debug):
    """Start WhatsApp/SMS conversational webhook server."""
    validate_setup()

    # Import here to avoid import errors if Flask not installed
    try:
        from webhook_server import app as flask_app
        from config import WEBHOOK_PORT
    except ImportError:
        console.print(
            "❌ [red]Flask and Twilio dependencies not installed[/red]\n"
            "   Run: pip install -r requirements.txt",
            style="bold red",
        )
        sys.exit(1)

    # Determine port
    run_port = port or WEBHOOK_PORT

    # Display startup info
    console.print(Panel("[bold cyan]WhatsApp/SMS Webhook Server[/bold cyan]", expand=False))
    console.print(f"[bold cyan]>> Webhook URL:[/bold cyan] [cyan]http://localhost:{run_port}/webhook[/cyan]\n")
    console.print("[bold]To expose publicly, use ngrok:[/bold]")
    console.print(f"   [yellow]ngrok http {run_port}[/yellow]\n")
    console.print("[bold]Then configure Twilio webhook endpoint to:[/bold]")
    console.print("   [yellow]https://<ngrok-url>.ngrok.io/webhook[/yellow]\n")
    console.print("[bold]Server starting...[/bold]\n")

    try:
        flask_app.run(host="0.0.0.0", port=run_port, debug=debug)
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.option("--date", default=None, help="Date in YYYY-MM-DD format (defaults to most recent)")
def report(date):
    """View saved report for a date."""
    from storage import load_insights

    try:
        if date:
            insights = load_insights(date)
            if not insights:
                console.print(f"❌ No report found for {date}")
                return
            title = f"EMAIL INSIGHTS — {date}"
        else:
            insights = get_most_recent_insights()
            if not insights:
                console.print("❌ No saved reports found")
                return
            title = "EMAIL INSIGHTS — MOST RECENT"

        print_report(insights, title)

    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    cli()
