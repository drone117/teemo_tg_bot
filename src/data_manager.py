"""Data management module for loading and saving baby status."""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Set Moscow timezone
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

DATA_DIR = Path(os.environ.get("BABY_BOT_DATA_DIR", "data"))
DATA_FILE = DATA_DIR / "status.json"

DEFAULT_USER_STATUS = {
    "feeding": "Unknown",
    "feeding_time": "Never",
    "sleeping": "Unknown",
    "sleeping_time": "Never",
    "woke_up": "Unknown",
    "woke_up_time": "Never",
    "history": [],
    "last_updated": "Never",
}

ACTION_EMOJIS = {
    "feeding": "🍼",
    "sleeping": "😴",
    "woke_up": "🌅",
}

ACTION_LABELS = {
    "feeding": "Feeding",
    "sleeping": "Sleeping",
    "woke_up": "Woke up",
}

HISTORY_LIMIT = 50


def load_status():
    """Load all users' baby status from file."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading status file: {e}")
            return {}
    return {}


def save_status(data):
    """Save all users' baby status to file."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.error(f"Error saving status file: {e}")


def get_user_status(user_id):
    """Get status for a specific user."""
    all_data = load_status()
    return all_data.get(str(user_id), dict(DEFAULT_USER_STATUS))


def update_user_status(user_id, action, status_value):
    """Update status for a specific user."""
    all_data = load_status()
    user_key = str(user_id)

    if user_key not in all_data:
        all_data[user_key] = dict(DEFAULT_USER_STATUS)

    now = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d %H:%M:%S")
    all_data[user_key][action] = status_value
    all_data[user_key][f"{action}_time"] = now
    all_data[user_key]["last_updated"] = now

    # Add to history
    if "history" not in all_data[user_key]:
        all_data[user_key]["history"] = []

    all_data[user_key]["history"].append({
        "action": action,
        "status": status_value,
        "time": now,
        "emoji": ACTION_EMOJIS.get(action, "❓"),
        "label": ACTION_LABELS.get(action, action.capitalize()),
    })

    # Keep only last N entries
    all_data[user_key]["history"] = all_data[user_key]["history"][-HISTORY_LIMIT:]

    save_status(all_data)
    return all_data[user_key]
