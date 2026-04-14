"""Main application entry point for the Telegram Baby Bot."""

import os
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from src.handlers import (
    start,
    help_command,
    status_command,
    button_handler,
    unknown_command,
    error_handler,
)

logger = logging.getLogger(__name__)


def create_application(token: str) -> Application:
    """Create and configure the Telegram bot application.

    Args:
        token: The Telegram bot token.

    Returns:
        Configured Application instance.
    """
    application = Application.builder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Register error handler
    application.add_error_handler(error_handler)

    return application


def main():
    """Start the bot."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

    if token == "your_bot_token_here":
        raise ValueError("Please set your actual bot token in the .env file")

    application = create_application(token)

    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
