#!/usr/bin/env python
"""Test script to validate Email Insights Agent setup."""

import sys
from pathlib import Path

def check_python():
    """Check Python version."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check required packages are installed."""
    required = [
        "anthropic",
        "google.auth",
        "google.oauth2",
        "googleapiclient",
        "click",
        "rich",
        "schedule",
        "dateutil",
    ]

    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False

    print(f"✅ All dependencies installed")
    return True

def check_credentials():
    """Check Google OAuth credentials file."""
    creds = Path(__file__).parent / "credentials.json"
    if not creds.exists():
        print("❌ credentials.json not found")
        print("   Download from Google Cloud Console and save here")
        return False
    print("✅ credentials.json found")
    return True

def check_api_key():
    """Check Anthropic API key."""
    import os
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   Run: export ANTHROPIC_API_KEY=sk-...")
        return False
    if not key.startswith("sk-"):
        print("⚠️  ANTHROPIC_API_KEY looks invalid (should start with sk-)")
        return False
    print("✅ ANTHROPIC_API_KEY configured")
    return True

def check_config():
    """Check config module loads."""
    try:
        import config
        print("✅ Config module loads")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def check_modules():
    """Check all main modules load."""
    modules = ["config", "storage", "gmail_client", "agent", "cron_runner", "main"]
    failed = []

    for mod in modules:
        try:
            __import__(mod)
        except Exception as e:
            failed.append(f"{mod}: {e}")

    if failed:
        print(f"❌ Module load failures:")
        for err in failed:
            print(f"   {err}")
        return False

    print(f"✅ All modules load successfully")
    return True

def main():
    """Run all checks."""
    print("🔍 Email Insights Agent Setup Check")
    print("=" * 40)
    print()

    checks = [
        ("Python version", check_python),
        ("Dependencies", check_dependencies),
        ("Google credentials", check_credentials),
        ("Anthropic API key", check_api_key),
        ("Configuration", check_config),
        ("Python modules", check_modules),
    ]

    results = []
    for name, check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ {name}: {e}")
            results.append(False)
        print()

    print("=" * 40)
    if all(results):
        print("✅ All checks passed! Ready to run:")
        print("   python main.py initial")
        return 0
    else:
        print("❌ Some checks failed. See above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
