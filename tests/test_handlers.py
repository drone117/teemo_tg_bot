"""Tests for src/handlers.py module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.handlers import (
    build_keyboard,
    start,
    help_command,
    status_command,
    button_handler,
    unknown_command,
    _handle_statistics,
    _handle_status_toggle,
)


class TestBuildKeyboard:
    """Tests for build_keyboard function."""

    def test_build_keyboard_returns_markup(self):
        """Test that build_keyboard returns InlineKeyboardMarkup."""
        markup = build_keyboard()
        assert markup is not None
        assert len(markup.inline_keyboard) == 4

    def test_build_keyboard_has_all_buttons(self):
        """Test that keyboard contains all expected buttons."""
        markup = build_keyboard()
        button_texts = [
            button.text
            for row in markup.inline_keyboard
            for button in row
        ]

        assert "🍼 Feeding" in button_texts
        assert "😴 Sleeping" in button_texts
        assert "🌅 Woke up" in button_texts
        assert "📊 View Statistics" in button_texts

    def test_build_keyboard_callback_data(self):
        """Test that buttons have correct callback data."""
        markup = build_keyboard()
        callback_data = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
        ]

        assert "feeding" in callback_data
        assert "sleeping" in callback_data
        assert "woke_up" in callback_data
        assert "statistics" in callback_data


class TestStartCommand:
    """Tests for /start command handler."""

    @pytest.mark.asyncio
    async def test_start_command_sends_message(self, mock_update_message, mock_context, fresh_data_dir):
        """Test that /start command sends a message."""
        await start(mock_update_message, mock_context)

        mock_update_message.message.reply_text.assert_called_once()
        call_args = mock_update_message.message.reply_text.call_args
        assert "Hi TestUser!" in call_args[0][0]
        assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_start_command_no_message(self, mock_context):
        """Test /start command with no message."""
        mock_update = MagicMock()
        mock_update.message = None

        result = await start(mock_update, mock_context)
        assert result is None


class TestHelpCommand:
    """Tests for /help command handler."""

    @pytest.mark.asyncio
    async def test_help_command_sends_message(self, mock_update_message, mock_context):
        """Test that /help command sends help text."""
        await help_command(mock_update_message, mock_context)

        mock_update_message.message.reply_text.assert_called_once()
        call_args = mock_update_message.message.reply_text.call_args
        assert "/start" in call_args[0][0]
        assert "/help" in call_args[0][0]
        assert "/status" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_help_command_no_message(self, mock_context):
        """Test /help command with no message."""
        mock_update = MagicMock()
        mock_update.message = None

        result = await help_command(mock_update, mock_context)
        assert result is None


class TestStatusCommand:
    """Tests for /status command handler."""

    @pytest.mark.asyncio
    async def test_status_command_sends_message(self, mock_update_message, mock_context, fresh_data_dir, sample_user_status):
        """Test that /status command sends status."""
        from src.data_manager import save_status
        save_status({"123": sample_user_status})

        await status_command(mock_update_message, mock_context)

        mock_update_message.message.reply_text.assert_called_once()
        call_args = mock_update_message.message.reply_text.call_args
        assert "Current baby status:" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_status_command_no_message(self, mock_context):
        """Test /status command with no message."""
        mock_update = MagicMock()
        mock_update.message = None

        result = await status_command(mock_update, mock_context)
        assert result is None


class TestHandleStatistics:
    """Tests for _handle_statistics internal function."""

    @pytest.mark.asyncio
    async def test_handle_statistics_edits_message(self, mock_query, fresh_data_dir, sample_user_status):
        """Test that handle statistics edits message."""
        from src.data_manager import save_status
        save_status({"123": sample_user_status})

        await _handle_statistics(mock_query, 123)

        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "Statistics Summary" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_statistics_sends_graph(self, mock_query, fresh_data_dir, sample_user_status):
        """Test that handle statistics sends graph."""
        from src.data_manager import save_status
        save_status({"123": sample_user_status})

        await _handle_statistics(mock_query, 123)

        mock_query.message.reply_photo.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_statistics_no_history(self, mock_query):
        """Test handle statistics with no history."""
        with patch("src.handlers.get_user_status") as mock_get:
            mock_get.return_value = {"history": [], "feeding": "Unknown", "sleeping": "Unknown", "woke_up": "Unknown"}
            await _handle_statistics(mock_query, 9001)

        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "No statistics available" in call_args[0][0]
        # No graph should be sent
        mock_query.message.reply_photo.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_statistics_edit_error(self, mock_query):
        """Test handle statistics when edit fails."""
        mock_query.edit_message_text = AsyncMock(side_effect=Exception("Edit failed"))

        await _handle_statistics(mock_query, 123)

        mock_query.answer.assert_called()
        call_args = mock_query.answer.call_args
        assert "Could not load statistics" in call_args[0][0]


class TestHandleStatusToggle:
    """Tests for _handle_status_toggle internal function."""

    @pytest.mark.asyncio
    async def test_handle_toggle_feeding(self, mock_query, fresh_data_dir):
        """Test handling feeding button toggle."""
        await _handle_status_toggle(mock_query, 123, "feeding")

        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "🍼 Feeding:" in call_args[0][0]
        assert "Hungry" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_toggle_sleeping(self, mock_query, fresh_data_dir):
        """Test handling sleeping button toggle."""
        await _handle_status_toggle(mock_query, 456, "sleeping")

        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "😴 Sleeping:" in call_args[0][0]
        assert "Awake" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_toggle_woke_up(self, mock_query, fresh_data_dir):
        """Test handling woke up button toggle."""
        await _handle_status_toggle(mock_query, 789, "woke_up")

        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "🌅 Woke up:" in call_args[0][0]
        assert "Just Woke Up" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_toggle_error(self, mock_query, fresh_data_dir):
        """Test handle toggle when edit fails."""
        mock_query.edit_message_text = AsyncMock(side_effect=Exception("Edit failed"))

        await _handle_status_toggle(mock_query, 111, "feeding")

        mock_query.answer.assert_called()
        call_args = mock_query.answer.call_args
        assert "Status updated" in call_args[0][0]


class TestButtonHandler:
    """Tests for button_handler."""

    @pytest.mark.asyncio
    async def test_button_handler_feeding(self, mock_query, fresh_data_dir):
        """Test handling feeding button."""
        mock_query.data = "feeding"
        mock_update = MagicMock()
        mock_update.callback_query = mock_query
        mock_context = MagicMock()

        await button_handler(mock_update, mock_context)

        mock_query.answer.assert_called_once()
        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "🍼 Feeding:" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_button_handler_statistics(self, mock_query, fresh_data_dir, sample_user_status):
        """Test handling statistics button."""
        from src.data_manager import save_status
        save_status({"123": sample_user_status})

        mock_query.data = "statistics"
        mock_update = MagicMock()
        mock_update.callback_query = mock_query

        mock_context = MagicMock()

        await button_handler(mock_update, mock_context)

        mock_query.edit_message_text.assert_called_once()
        call_args = mock_query.edit_message_text.call_args
        assert "Statistics Summary" in call_args[0][0]
        mock_query.message.reply_photo.assert_called_once()

    @pytest.mark.asyncio
    async def test_button_handler_unknown(self, mock_query):
        """Test handling unknown button."""
        mock_query.data = "unknown_action"
        mock_update = MagicMock()
        mock_update.callback_query = mock_query

        mock_context = MagicMock()

        await button_handler(mock_update, mock_context)

        mock_query.answer.assert_called()
        mock_query.edit_message_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_button_handler_no_query(self, mock_context):
        """Test button handler with no callback query."""
        mock_update = MagicMock()
        mock_update.callback_query = None

        result = await button_handler(mock_update, mock_context)
        assert result is None

    @pytest.mark.asyncio
    async def test_button_handler_cycles_status(self, mock_query, fresh_data_dir):
        """Test that button cycles through statuses."""
        mock_query.data = "feeding"
        mock_update = MagicMock()
        mock_update.callback_query = mock_query
        mock_context = MagicMock()

        # First press: Unknown -> Hungry
        await button_handler(mock_update, mock_context)
        call_args = mock_query.edit_message_text.call_args
        assert "Hungry" in call_args[0][0]

        # Reset mock
        mock_query.edit_message_text.reset_mock()

        # Second press: Hungry -> Fed
        await button_handler(mock_update, mock_context)
        call_args = mock_query.edit_message_text.call_args
        assert "Fed" in call_args[0][0]

        # Reset mock
        mock_query.edit_message_text.reset_mock()

        # Third press: Fed -> Burping
        await button_handler(mock_update, mock_context)
        call_args = mock_query.edit_message_text.call_args
        assert "Burping" in call_args[0][0]

        # Fourth press: Burping -> Hungry (cycle back)
        mock_query.edit_message_text.reset_mock()
        await button_handler(mock_update, mock_context)
        call_args = mock_query.edit_message_text.call_args
        assert "Hungry" in call_args[0][0]


class TestUnknownCommand:
    """Tests for unknown_command handler."""

    @pytest.mark.asyncio
    async def test_unknown_command_handler(self, mock_update_message, mock_context):
        """Test handling of unknown commands."""
        mock_update_message.message.text = "/unknown"

        await unknown_command(mock_update_message, mock_context)

        mock_update_message.message.reply_text.assert_called_once()
        call_args = mock_update_message.message.reply_text.call_args
        assert "don't recognize that command" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_unknown_command_ignores_non_command(self, mock_update_message, mock_context):
        """Test that non-commands are ignored."""
        mock_update_message.message.text = "not a command"

        await unknown_command(mock_update_message, mock_context)

        mock_update_message.message.reply_text.assert_not_called()
