"""Local JSON storage for insights and run history."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import DATA_DIR, INSIGHTS_DIR, LAST_RUN_FILE


def save_insights(insights: Dict[str, Any], date_str: str) -> Path:
    """
    Save insights to JSON file.

    Args:
        insights: The analysis results dictionary
        date_str: Date string for filename (YYYY-MM-DD format)

    Returns:
        Path to saved file
    """
    file_path = INSIGHTS_DIR / f"insights_{date_str}.json"
    with open(file_path, "w") as f:
        json.dump(insights, f, indent=2, default=str)
    return file_path


def load_insights(date_str: str) -> Optional[Dict[str, Any]]:
    """
    Load insights from JSON file.

    Args:
        date_str: Date string for filename (YYYY-MM-DD format)

    Returns:
        Insights dictionary or None if not found
    """
    file_path = INSIGHTS_DIR / f"insights_{date_str}.json"
    if not file_path.exists():
        return None

    with open(file_path, "r") as f:
        return json.load(f)


def save_last_run(dt: datetime) -> None:
    """Save timestamp of last run."""
    data = {"last_run": dt.isoformat()}
    with open(LAST_RUN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_last_run() -> Optional[datetime]:
    """Load timestamp of last run."""
    if not LAST_RUN_FILE.exists():
        return None

    with open(LAST_RUN_FILE, "r") as f:
        data = json.load(f)

    last_run_str = data.get("last_run")
    if last_run_str:
        return datetime.fromisoformat(last_run_str)
    return None


def load_all_insights() -> List[Dict[str, Any]]:
    """Load all saved insights for trend analysis."""
    insights_list = []

    if not INSIGHTS_DIR.exists():
        return insights_list

    for file_path in sorted(INSIGHTS_DIR.glob("insights_*.json")):
        with open(file_path, "r") as f:
            insights_list.append(json.load(f))

    return insights_list


def get_most_recent_insights() -> Optional[Dict[str, Any]]:
    """Load the most recently saved insights."""
    if not INSIGHTS_DIR.exists():
        return None

    files = sorted(INSIGHTS_DIR.glob("insights_*.json"), reverse=True)
    if not files:
        return None

    with open(files[0], "r") as f:
        return json.load(f)
