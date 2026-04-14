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
    "feeding": ["Hungry", "Fed", "Burping"],
    "sleeping": ["Awake", "Sleeping", "Deep Sleep"],
    "woke_up": ["Just Woke Up", "Fresh", "Active"],
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


def build_keyboard():
    """Build the inline keyboard with action buttons."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍼 Feeding", callback_data="feeding")],
        [InlineKeyboardButton("😴 Sleeping", callback_data="sleeping")],
        [InlineKeyboardButton("🌅 Woke up", callback_data="woke_up")],
        [InlineKeyboardButton("📊 View Statistics", callback_data="statistics")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if update.message is None:
        return

    user_id = update.message.from_user.id
    user_status = get_user_status(user_id)

    await update.message.reply_text(
        f"Hi {update.message.from_user.first_name}! I'm a baby bot.\n\n"
        f"Current status:\n"
        f"{format_status(user_status)}\n\n"
        "Tap a button to update the status:",
        reply_markup=build_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    if update.message is None:
        return

    await update.message.reply_text(
        "Available commands:\n"
        "/start - Show the status menu\n"
        "/help - Show this help message\n"
        "/status - View current status without buttons\n\n"
        "Use the buttons to check or update baby status.\n"
        "Each tap cycles through status options."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /status is issued."""
    if update.message is None:
        return

    user_id = update.message.from_user.id
    user_status = get_user_status(user_id)

    await update.message.reply_text(
        f"Current baby status:\n{format_status(user_status)}"
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
        await query.answer("Could not load statistics!")
        return

    # Generate and send graph
    graph_buf = generate_schedule_graph(user_status)
    if graph_buf:
        try:
            await query.message.reply_photo(
                photo=graph_buf,
                caption="📊 Baby's Schedule Timeline",
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
            f"Current status:\n"
            f"{format_status(user_status)}",
            parse_mode="Markdown",
            reply_markup=build_keyboard(),
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        await query.answer("Status updated!")


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
        await query.answer("Unknown action")
        return

    await _handle_status_toggle(query, user_id, action)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands."""
    if update.message and update.message.text and update.message.text.startswith('/'):
        await update.message.reply_text(
            "Sorry, I don't recognize that command. Use /help to see available commands."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
