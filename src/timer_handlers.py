"""Simplified handlers using the new timer-based approach."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from src.timer_manager import BabyScheduleManager, ACTIVITIES
from src.graph_generator_plotly import generate_schedule_graph

logger = logging.getLogger(__name__)

# Store user timers
user_timers = {}

# Track bot messages per user to prevent spam (only 1 menu + 1 image at a time)
_user_messages = {}  # user_id -> {"status_msg_id": int, "chat_id": int, "graph_msg_id": int}


def get_user_timer(user_id: int) -> BabyScheduleManager:
    """Get or create timer manager for user."""
    if user_id not in user_timers:
        user_timers[user_id] = BabyScheduleManager(user_id)
    return user_timers[user_id]


def build_keyboard_from_timer(timer_manager: BabyScheduleManager) -> InlineKeyboardMarkup:
    """Build keyboard based on current timer state."""
    buttons = timer_manager.get_activity_buttons()

    # Convert to InlineKeyboardMarkup
    inline_buttons = []
    for row in buttons:
        button_row = []
        for button in row:
            button_row.append(
                InlineKeyboardButton(button["text"], callback_data=button["callback_data"])
            )
        inline_buttons.append(button_row)

    return InlineKeyboardMarkup(inline_buttons)


async def _cleanup_user_messages(user_id: int, bot, chat_id: int):
    """Delete previous bot messages for user to prevent spam."""
    if user_id not in _user_messages:
        return

    msgs = _user_messages[user_id]
    if msgs.get("chat_id") != chat_id:
        return

    for key in ("status_msg_id", "graph_msg_id"):
        msg_id = msgs.get(key)
        if msg_id:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass

    _user_messages.pop(user_id, None)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if update.message is None:
        return

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    timer_manager = get_user_timer(user_id)

    # Delete old bot messages to prevent spam
    await _cleanup_user_messages(user_id, context.bot, chat_id)

    status_text = timer_manager.get_simple_status_text()
    suggestions = timer_manager.get_status_summary().get("suggestions", [])

    message = f"👋 Привет {update.message.from_user.first_name}!\n\n"
    message += f"{status_text}\n\n"

    if suggestions:
        message += "💡 " + suggestions[0] + "\n\n"

    message += "Нажмите кнопку, чтобы начать занятие:"

    sent_msg = await update.message.reply_text(
        message,
        reply_markup=build_keyboard_from_timer(timer_manager)
    )

    # Track this message for cleanup
    _user_messages[user_id] = {
        "status_msg_id": sent_msg.message_id,
        "chat_id": chat_id,
        "graph_msg_id": None
    }


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    if update.message is None:
        return

    help_text = """
🤱 **Помощь по отслеживанию режима**

**Основные команды:**
/start - Показать текущий статус и кнопки
/help - Показать эту справку

**Как пользоваться:**

📱 **Таймерная система:**
• Нажмите кнопку начала занятия (кормление/сон/бодрствование)
• Таймер автоматически отсчитывает время
• Нажмите остановить, когда занятие закончилось

📊 **Преимущества:**
• Простое управление - всего 2 действия
• Автоматический подсчет времени
• Умные предложения на основе шаблонов
• Статистика и аналитика

💡 **Советы:**
• Не нажимайте кнопки слишком часто
• Давайте ребенку время на занятия
• Система подскажет, когда пора что-то изменить

Для вопросов и предложений: @your_username
    """

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send current status without buttons."""
    if update.message is None:
        return

    user_id = update.message.from_user.id
    timer_manager = get_user_timer(user_id)

    status_text = timer_manager.get_simple_status_text()
    await update.message.reply_text(f"Текущий статус: {status_text}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle simplified button interactions."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    user_id = query.from_user.id
    timer_manager = get_user_timer(user_id)

    action = query.data

    # Handle different actions
    if action.startswith("start_"):
        activity_type = action.replace("start_", "")
        status_summary = timer_manager.start_activity(activity_type)

        message = format_status_message(status_summary)

    elif action == "stop_current":
        status_summary = timer_manager.stop_current_activity()
        message = format_status_message(status_summary)

    elif action == "current_status":
        # Just show current status
        status_summary = timer_manager.get_status_summary()
        message = format_status_message(status_summary)

    elif action == "statistics":
        await handle_statistics(query, context, timer_manager)
        return

    else:
        message = "❓ Неизвестное действие"

    try:
        await query.edit_message_text(
            message,
            reply_markup=build_keyboard_from_timer(timer_manager)
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        await query.answer("Статус обновлён!")


def format_status_message(status_summary: dict) -> str:
    """Format status summary into readable message."""
    if status_summary["status"] == "idle":
        message = "😴 **Нет активного занятия**\n\n"
        suggestions = status_summary.get("suggestions", [])
        if suggestions:
            message += "💡 " + suggestions[0]
        return message

    current = status_summary["current_activity"]
    message = f"{current['emoji']} **{current['name']}**\n\n"
    message += f"⏱️ Длительность: {current['duration_str']}\n"
    message += f"🕒 Начало: {current['start_time']}\n"

    suggestions = status_summary.get("suggestions", [])
    if suggestions:
        message += "\n💡 " + suggestions[0]

    return message


def convert_timer_history_to_graph_format(timer_manager: BabyScheduleManager) -> dict:
    """Convert timer manager's activity history to old-format for graph generation.

    Only includes activities from the last 24 hours.
    """
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    TYPE_TO_OLD = {
        "feed": ("feeding", "Покормлен", "🍼", "Кормление"),
        "sleep": ("sleeping", "Спит", "😴", "Сон"),
        "wake": ("woke_up", "Отдохнувший", "🌅", "Бодрствование"),
    }

    cutoff = datetime.now(ZoneInfo("Europe/Moscow")) - timedelta(hours=24)
    history = []

    for activity in timer_manager.activity_history:
        entry = activity.to_dict()
        if entry["end_time"] is None:
            continue

        # Skip activities older than 24 hours
        start_dt = datetime.strptime(entry["start_time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo("Europe/Moscow"))
        if start_dt < cutoff:
            continue

        action, status, emoji, label = TYPE_TO_OLD[entry["type"]]

        history.append({
            "action": action,
            "status": status,
            "time": entry["start_time"],
            "emoji": emoji,
            "label": label,
        })

        if entry["type"] == "sleep":
            history.append({
                "action": "woke_up",
                "status": "Отдохнувший",
                "time": entry["end_time"],
                "emoji": "🌅",
                "label": "Бодрствование",
            })

    if timer_manager.current_activity and timer_manager.current_activity.is_running:
        entry = timer_manager.current_activity.to_dict()
        action, status, emoji, label = TYPE_TO_OLD[entry["type"]]
        history.append({
            "action": action,
            "status": status,
            "time": entry["start_time"],
            "emoji": emoji,
            "label": label,
        })

    history.sort(key=lambda x: x["time"])
    return {"history": history}


async def handle_statistics(query, context, timer_manager: BabyScheduleManager):
    """Handle statistics display with graph."""
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    stats = timer_manager.get_statistics_summary()

    if stats["total_activities"] == 0:
        message = "📊 **Статистика пуста**\n\n"
        message += "Начните отслеживание, нажав кнопку начала занятия!"
    else:
        message = f"📊 **Статистика за {stats['today_date']}**\n\n"

        if stats["today_summary"]:
            message += "📈 **Сегодняшняя активность:**\n"
            for line in stats["today_summary"]:
                message += f"• {line}\n"
        else:
            message += "Сегодня еще нет записей\n"

        message += f"\n📝 Всего записей: {stats['total_activities']}"

    try:
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=build_keyboard_from_timer(timer_manager),
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        await query.answer("Не удалось загрузить статистику!")
        return

    # Generate and send graph
    graph_data = convert_timer_history_to_graph_format(timer_manager)
    graph_buf = generate_schedule_graph(graph_data)
    if not graph_buf:
        return

    caption = "📊 Временная шкала режима ребёнка"
    old_graph_msg_id = _user_messages.get(user_id, {}).get("graph_msg_id")

    if old_graph_msg_id:
        # Try to edit existing graph message to avoid spam
        try:
            await context.bot.edit_message_media(
                chat_id=chat_id,
                message_id=old_graph_msg_id,
                media=InputMediaPhoto(media=graph_buf, caption=caption)
            )
            return
        except Exception as e:
            logger.debug(f"Could not edit graph message, sending new: {e}")
            # Old message may be gone, clean up and send new
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=old_graph_msg_id)
            except Exception:
                pass

    # Send new graph message
    sent_msg = await query.message.reply_photo(
        photo=graph_buf,
        caption=caption,
    )

    # Track graph message for reuse
    if user_id not in _user_messages:
        _user_messages[user_id] = {"chat_id": chat_id}
    _user_messages[user_id]["graph_msg_id"] = sent_msg.message_id


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands."""
    if update.message and update.message.text and update.message.text.startswith('/'):
        await update.message.reply_text(
            "Извините, я не распознал эту команду. Используйте /help для просмотра доступных команд."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)