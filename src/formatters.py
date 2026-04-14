"""Formatting functions for displaying baby status and statistics."""


def format_status(user_status):
    """Format user status for display."""
    return (
        f"🍼 Кормление: {user_status['feeding']}\n"
        f"   🕒 {user_status['feeding_time']}\n"
        f"😴 Сон: {user_status['sleeping']}\n"
        f"   🕒 {user_status['sleeping_time']}\n"
        f"🌅 Проснулся: {user_status['woke_up']}\n"
        f"   🕒 {user_status['woke_up_time']}\n"
        f"📝 Последнее обновление: {user_status['last_updated']}"
    )


def format_statistics(user_status):
    """Format user statistics for display."""
    history = user_status.get("history", [])

    if not history:
        return "Статистики пока нет. Начните отслеживание, нажимая кнопки!"

    # Count occurrences
    feeding_count = sum(1 for h in history if h["action"] == "feeding")
    sleeping_count = sum(1 for h in history if h["action"] == "sleeping")
    woke_up_count = sum(1 for h in history if h["action"] == "woke_up")

    stats_text = (
        f"*📊 Сводка статистики*\n\n"
        f"🍼 Обновлений кормления: {feeding_count}\n"
        f"😴 Обновлений сна: {sleeping_count}\n"
        f"🌅 Обновлений пробуждения: {woke_up_count}\n"
        f"📝 Всего обновлений: {len(history)}\n\n"
        f"*Последняя история (последние 10):*\n"
    )

    # Show last 10 entries
    recent = history[-10:]
    for entry in reversed(recent):
        stats_text += f"{entry['emoji']} {entry['label']}: {entry['status']} в {entry['time']}\n"

    return stats_text
