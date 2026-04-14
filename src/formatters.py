"""Formatting functions for displaying baby status and statistics."""


def format_status(user_status):
    """Format user status for display."""
    return (
        f"🍼 Feeding: {user_status['feeding']}\n"
        f"   🕒 {user_status['feeding_time']}\n"
        f"😴 Sleeping: {user_status['sleeping']}\n"
        f"   🕒 {user_status['sleeping_time']}\n"
        f"🌅 Woke up: {user_status['woke_up']}\n"
        f"   🕒 {user_status['woke_up_time']}\n"
        f"📝 Last updated: {user_status['last_updated']}"
    )


def format_statistics(user_status):
    """Format user statistics for display."""
    history = user_status.get("history", [])

    if not history:
        return "No statistics available yet. Start tracking by pressing the buttons!"

    # Count occurrences
    feeding_count = sum(1 for h in history if h["action"] == "feeding")
    sleeping_count = sum(1 for h in history if h["action"] == "sleeping")
    woke_up_count = sum(1 for h in history if h["action"] == "woke_up")

    stats_text = (
        f"*📊 Statistics Summary*\n\n"
        f"🍼 Feeding updates: {feeding_count}\n"
        f"😴 Sleeping updates: {sleeping_count}\n"
        f"🌅 Woke up updates: {woke_up_count}\n"
        f"📝 Total updates: {len(history)}\n\n"
        f"*Recent History (last 10):*\n"
    )

    # Show last 10 entries
    recent = history[-10:]
    for entry in reversed(recent):
        stats_text += f"{entry['emoji']} {entry['label']}: {entry['status']} at {entry['time']}\n"

    return stats_text
