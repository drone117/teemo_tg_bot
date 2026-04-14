"""Telegram bot command handlers."""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.data_manager import get_user_status, update_user_status
from src.formatters import format_status, format_statistics
from src.graph_generator import generate_schedule_graph

logger = logging.getLogger(__name__)

# Status cycling options
STATUS_OPTIONS = {
    "feeding": ["Голоден", "Покормлен", "Срыгивает"],
    "sleeping": ["Бодрствует", "Спит", "Глубокий сон"],
    "woke_up": ["Только проснулся", "Отдохнувший", "Активный"],
}

ACTION_EMOJIS = {
    "feeding": "🍼",
    "sleeping": "😴",
    "woke_up": "🌅",
}

ACTION_LABELS = {
    "feeding": "Кормление",
    "sleeping": "Сон",
    "woke_up": "Проснулся",
}


def build_keyboard():
    """Build the inline keyboard with action buttons."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍼 Кормление", callback_data="feeding")],
        [InlineKeyboardButton("😴 Сон", callback_data="sleeping")],
        [InlineKeyboardButton("🌅 Проснулся", callback_data="woke_up")],
        [InlineKeyboardButton("📊 Посмотреть статистику", callback_data="statistics")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if update.message is None:
        return

    user_id = update.message.from_user.id
    user_status = get_user_status(user_id)

    await update.message.reply_text(
        f"Привет {update.message.from_user.first_name}! Я бот для отслеживания режима ребёнка.\n\n"
        f"Текущий статус:\n"
        f"{format_status(user_status)}\n\n"
        f"Нажмите кнопку, чтобы обновить статус:",
        reply_markup=build_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    if update.message is None:
        return

    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Показать меню статуса\n"
        "/help - Показать эту справку\n"
        "/status - Просмотреть текущий статус без кнопок\n\n"
        "Используйте кнопки для проверки или обновления статуса ребёнка.\n"
        "Каждое нажатие переключает варианты статуса."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /status is issued."""
    if update.message is None:
        return

    user_id = update.message.from_user.id
    user_status = get_user_status(user_id)

    await update.message.reply_text(
        f"Текущий статус ребёнка:\n{format_status(user_status)}"
    )


async def _handle_statistics(query, user_id):
    """Handle the statistics button press."""
    user_status = get_user_status(user_id)
    stats_text = format_statistics(user_status)

    try:
        await query.edit_message_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=build_keyboard(),
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        await query.answer("Не удалось загрузить статистику!")
        return

    # Generate and send graph
    graph_buf = generate_schedule_graph(user_status)
    if graph_buf:
        try:
            await query.message.reply_photo(
                photo=graph_buf,
                caption="📊 Временная шкала режима ребёнка",
            )
        except Exception as e:
            logger.error(f"Error sending graph: {e}")


async def _handle_status_toggle(query, user_id, action):
    """Handle feeding/sleeping/woke_up button press."""
    options = STATUS_OPTIONS[action]

    user_status = get_user_status(user_id)
    current = user_status.get(action, "Unknown")
    idx = (options.index(current) + 1) % len(options) if current in options else 0
    new_status = options[idx]

    user_status = update_user_status(user_id, action, new_status)

    emoji = ACTION_EMOJIS[action]
    label = ACTION_LABELS[action]

    try:
        await query.edit_message_text(
            f"{emoji} {label}: *{new_status}*\n\n"
            f"Текущий статус:\n"
            f"{format_status(user_status)}",
            parse_mode="Markdown",
            reply_markup=build_keyboard(),
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        await query.answer("Статус обновлён!")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    user_id = query.from_user.id
    action = query.data

    # Handle statistics separately
    if action == "statistics":
        await _handle_statistics(query, user_id)
        return

    # Handle status toggle
    if action not in STATUS_OPTIONS:
        logger.error(f"Unknown action: {action}")
        await query.answer("Неизвестное действие")
        return

    await _handle_status_toggle(query, user_id, action)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands."""
    if update.message and update.message.text and update.message.text.startswith('/'):
        await update.message.reply_text(
            "Извините, я не распознал эту команду. Используйте /help для просмотра доступных команд."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
