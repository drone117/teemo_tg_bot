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


def build_keyboard(user_status=None):
    """Build the inline keyboard with action buttons.
    
    Args:
        user_status: Optional dict containing current status. If provided, 
                     button texts will reflect current status values.
    """
    if user_status:
        feeding_text = f"{ACTION_EMOJIS['feeding']} {user_status.get('feeding', 'Unknown')}"
        sleeping_text = f"{ACTION_EMOJIS['sleeping']} {user_status.get('sleeping', 'Unknown')}"
        woke_up_text = f"{ACTION_EMOJIS['woke_up']} {user_status.get('woke_up', 'Unknown')}"
    else:
        feeding_text = f"{ACTION_EMOJIS['feeding']} {STATUS_OPTIONS['feeding'][0]}"
        sleeping_text = f"{ACTION_EMOJIS['sleeping']} {STATUS_OPTIONS['sleeping'][0]}"
        woke_up_text = f"{ACTION_EMOJIS['woke_up']} {STATUS_OPTIONS['woke_up'][0]}"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(feeding_text, callback_data="feeding")],
        [InlineKeyboardButton(sleeping_text, callback_data="sleeping")],
        [InlineKeyboardButton(woke_up_text, callback_data="woke_up")],
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
        reply_markup=build_keyboard(user_status),
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


async def _handle_statistics(query, user_id, context):
    """Handle the statistics button press."""
    from src.data_manager import load_status, save_status
    
    user_status = get_user_status(user_id)
    stats_text = format_statistics(user_status)

    # Delete previous graph message if it exists
    all_data = load_status()
    user_key = str(user_id)
    last_graph_message_id = all_data.get(user_key, {}).get("last_graph_message_id")
    
    if last_graph_message_id is not None:
        try:
            await context.bot.delete_message(
                chat_id=query.message.chat_id,
                message_id=last_graph_message_id
            )
        except Exception as e:
            logger.error(f"Error deleting previous graph message: {e}")
        # Clear the stored message ID
        if user_key in all_data:
            all_data[user_key]["last_graph_message_id"] = None
            save_status(all_data)

    # Try to edit the message, but ignore if content is the same
    try:
        await query.edit_message_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=build_keyboard(user_status),
        )
    except Exception as e:
        if "not modified" not in str(e).lower():
            logger.error(f"Error editing message: {e}")
            await query.answer("Не удалось загрузить статистику!")
            return
        # If message is not modified, that's okay - we still want to send the new graph
        logger.debug("Message content unchanged, proceeding to generate new graph")

    # Generate and send graph
    graph_buf = generate_schedule_graph(user_status)
    if graph_buf:
        try:
            graph_message = await query.message.reply_photo(
                photo=graph_buf,
                caption="📊 Временная шкала режима ребёнка",
            )
            # Store the message ID for later deletion
            all_data = load_status()
            if user_key in all_data:
                all_data[user_key]["last_graph_message_id"] = graph_message.message_id
                save_status(all_data)
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
            reply_markup=build_keyboard(user_status),
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
        await _handle_statistics(query, user_id, context)
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
