"""Tests for src/timer_handlers.py module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.timer_handlers import (
    start,
    help_command,
    status_command,
    button_handler,
    unknown_command,
    format_status_message,
    handle_statistics,
    convert_timer_history_to_graph_format,
    build_keyboard_from_timer,
)
from src.timer_manager import BabyScheduleManager, ActivityTimer


class TestBuildKeyboardFromTimer:
    """Tests for build_keyboard_from_timer function."""

    def test_idle_keyboard_has_start_buttons(self):
        """Test that idle keyboard shows start activity buttons."""
        manager = BabyScheduleManager(99999)
        # Clear any loaded history
        manager.activity_history = []
        manager.current_activity = None

        markup = build_keyboard_from_timer(manager)
        button_texts = [
            button.text
            for row in markup.inline_keyboard
            for button in row
        ]

        assert "🍼 Начать кормление" in button_texts
        assert "😴 Начать сон" in button_texts
        assert "🌅 Начать бодрствование" in button_texts
        assert "📊 Статистика" in button_texts

    def test_active_keyboard_has_stop_button(self):
        """Test that active keyboard shows stop button."""
        manager = BabyScheduleManager(99999)
        manager.current_activity = ActivityTimer("feed")
        manager.current_activity.start()

        markup = build_keyboard_from_timer(manager)
        button_texts = [
            button.text
            for row in markup.inline_keyboard
            for button in row
        ]

        assert any("Остановить" in text for text in button_texts)
        assert "📊 Статистика" in button_texts


class TestFormatStatusMessage:
    """Tests for format_status_message function."""

    def test_idle_status(self):
        """Test formatting idle status."""
        summary = {"status": "idle", "suggestions": ["Начните кормление"]}
        result = format_status_message(summary)
        assert "Нет активного занятия" in result
        assert "Начните кормление" in result

    def test_active_status(self):
        """Test formatting active status."""
        summary = {
            "status": "active",
            "current_activity": {
                "emoji": "🍼",
                "name": "Кормление",
                "duration_str": "15минут",
                "start_time": "10:00",
            },
            "suggestions": ["Продолжайте еще 5минут"],
        }
        result = format_status_message(summary)
        assert "Кормление" in result
        assert "15минут" in result
        assert "10:00" in result
        assert "Продолжайте" in result


class TestStartCommand:
    """Tests for /start command handler."""

    @pytest.mark.asyncio
    async def test_start_sends_message(self, mock_update_message, mock_context, fresh_data_dir):
        """Test that /start sends a welcome message."""
        await start(mock_update_message, mock_context)

        mock_update_message.message.reply_text.assert_called_once()
        call_args = mock_update_message.message.reply_text.call_args
        assert "Привет" in call_args[0][0]
        assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_start_no_message(self, mock_context):
        """Test /start with no message."""
        mock_update = MagicMock()
        mock_update.message = None
        result = await start(mock_update, mock_context)
        assert result is None


class TestHelpCommand:
    """Tests for /help command handler."""

    @pytest.mark.asyncio
    async def test_help_sends_message(self, mock_update_message, mock_context):
        """Test that /help sends help text."""
        await help_command(mock_update_message, mock_context)

        mock_update_message.message.reply_text.assert_called_once()
        call_args = mock_update_message.message.reply_text.call_args
        assert "/start" in call_args[0][0]
        assert "/help" in call_args[0][0]


class TestStatusCommand:
    """Tests for /status command handler."""

    @pytest.mark.asyncio
    async def test_status_sends_message(self, mock_update_message, mock_context, fresh_data_dir):
        """Test that /status sends status text."""
        await status_command(mock_update_message, mock_context)

        mock_update_message.message.reply_text.assert_called_once()
        call_args = mock_update_message.message.reply_text.call_args
        assert "статус" in call_args[0][0].lower()


class TestButtonHandler:
    """Tests for button_handler."""

    @pytest.mark.asyncio
    async def test_start_feed(self, fresh_data_dir):
        """Test starting a feed activity."""
        mock_query = AsyncMock()
        mock_query.from_user.id = 123
        mock_query.data = "start_feed"
        mock_query.answer = AsyncMock()
        mock_query.edit_message_text = AsyncMock()

        mock_update = MagicMock()
        mock_update.callback_query = mock_query
        mock_context = MagicMock()

        await button_handler(mock_update, mock_context)

        mock_query.answer.assert_called_once()
        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "Кормление" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_start_sleep(self, fresh_data_dir):
        """Test starting a sleep activity."""
        mock_query = AsyncMock()
        mock_query.from_user.id = 123
        mock_query.data = "start_sleep"
        mock_query.answer = AsyncMock()
        mock_query.edit_message_text = AsyncMock()

        mock_update = MagicMock()
        mock_update.callback_query = mock_query
        mock_context = MagicMock()

        await button_handler(mock_update, mock_context)

        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "Сон" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_stop_current(self, fresh_data_dir):
        """Test stopping current activity."""
        mock_query = AsyncMock()
        mock_query.from_user.id = 123
        mock_query.answer = AsyncMock()
        mock_query.edit_message_text = AsyncMock()

        mock_update = MagicMock()
        mock_update.callback_query = mock_query
        mock_context = MagicMock()

        # First start an activity
        mock_query.data = "start_feed"
        await button_handler(mock_update, mock_context)

        # Now stop it
        mock_query.edit_message_text.reset_mock()
        mock_query.data = "stop_current"
        await button_handler(mock_update, mock_context)

        call_args = mock_query.edit_message_text.call_args
        assert "Нет активного занятия" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_unknown_action(self, fresh_data_dir):
        """Test handling unknown action."""
        mock_query = AsyncMock()
        mock_query.from_user.id = 123
        mock_query.data = "unknown_action"
        mock_query.answer = AsyncMock()
        mock_query.edit_message_text = AsyncMock()

        mock_update = MagicMock()
        mock_update.callback_query = mock_query
        mock_context = MagicMock()

        await button_handler(mock_update, mock_context)

        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "Неизвестное действие" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_no_query(self, mock_context):
        """Test button handler with no callback query."""
        mock_update = MagicMock()
        mock_update.callback_query = None
        result = await button_handler(mock_update, mock_context)
        assert result is None


class TestConvertTimerHistoryToGraphFormat:
    """Tests for convert_timer_history_to_graph_format."""

    def test_empty_history(self):
        """Test with no activity history."""
        manager = BabyScheduleManager(99999)
        manager.activity_history = []
        manager.current_activity = None

        result = convert_timer_history_to_graph_format(manager)
        assert result == {"history": []}

    def test_feed_converted(self):
        """Test feed activity conversion."""
        manager = BabyScheduleManager(99999)
        timer = ActivityTimer("feed")
        timer.start_time = __import__('datetime').datetime.now(
            __import__('zoneinfo').ZoneInfo("Europe/Moscow")
        )
        timer.end_time = timer.start_time + __import__('datetime').timedelta(minutes=20)
        timer.is_running = False
        manager.activity_history = [timer]
        manager.current_activity = None

        result = convert_timer_history_to_graph_format(manager)
        assert len(result["history"]) == 1
        assert result["history"][0]["action"] == "feeding"
        assert result["history"][0]["status"] == "Покормлен"

    def test_sleep_converted_with_end(self):
        """Test sleep activity creates two entries (start + woke_up)."""
        manager = BabyScheduleManager(99999)
        timer = ActivityTimer("sleep")
        timer.start_time = __import__('datetime').datetime.now(
            __import__('zoneinfo').ZoneInfo("Europe/Moscow")
        )
        timer.end_time = timer.start_time + __import__('datetime').timedelta(hours=2)
        timer.is_running = False
        manager.activity_history = [timer]
        manager.current_activity = None

        result = convert_timer_history_to_graph_format(manager)
        assert len(result["history"]) == 2
        assert result["history"][0]["action"] == "sleeping"
        assert result["history"][0]["status"] == "Спит"
        assert result["history"][1]["action"] == "woke_up"

    def test_running_activity_included(self):
        """Test that currently running activity is included."""
        manager = BabyScheduleManager(99999)
        timer = ActivityTimer("wake")
        timer.start_time = __import__('datetime').datetime.now(
            __import__('zoneinfo').ZoneInfo("Europe/Moscow")
        )
        timer.is_running = True
        manager.activity_history = []
        manager.current_activity = timer

        result = convert_timer_history_to_graph_format(manager)
        assert len(result["history"]) == 1
        assert result["history"][0]["action"] == "woke_up"


class TestUnknownCommand:
    """Tests for unknown_command handler."""

    @pytest.mark.asyncio
    async def test_unknown_command(self, mock_update_message, mock_context):
        """Test handling unknown commands."""
        mock_update_message.message.text = "/unknown"
        await unknown_command(mock_update_message, mock_context)

        mock_update_message.message.reply_text.assert_called_once()
        call_args = mock_update_message.message.reply_text.call_args
        assert "не распознал" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_ignores_non_command(self, mock_update_message, mock_context):
        """Test that non-commands are ignored."""
        mock_update_message.message.text = "not a command"
        await unknown_command(mock_update_message, mock_context)
        mock_update_message.message.reply_text.assert_not_called()
