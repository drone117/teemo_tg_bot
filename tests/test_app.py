"""Tests for src/app_timer.py module."""

import os
from unittest.mock import patch, MagicMock

import pytest

from src.app_timer import create_application, main


class TestCreateApplication:
    """Tests for create_application function."""

    def test_create_application_returns_instance(self):
        """Test that create_application returns an Application."""
        app = create_application("fake_token_123")
        assert app is not None

    def test_create_application_registers_handlers(self):
        """Test that application has handlers registered."""
        app = create_application("fake_token_123")
        # Check that handlers list is not empty
        assert len(app.handlers) > 0

    def test_create_application_registers_error_handler(self):
        """Test that application has error handler registered."""
        app = create_application("fake_token_123")
        assert len(app.error_handlers) > 0


class TestMain:
    """Tests for main function."""

    def test_main_raises_error_when_no_token(self):
        """Test that main raises ValueError when no token is set."""
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}, clear=True):
            with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
                main()

    def test_main_raises_error_when_placeholder_token(self):
        """Test that main raises ValueError when placeholder token is used."""
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "your_bot_token_here"}, clear=True):
            with pytest.raises(ValueError, match="actual bot token"):
                main()

    def test_main_calls_run_polling(self):
        """Test that main calls run_polling on the application."""
        mock_app = MagicMock()
        with patch("src.app_timer.create_application", return_value=mock_app):
            with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"}, clear=True):
                with patch("src.app_timer.Update") as mock_update:
                    mock_update.ALL_TYPES = MagicMock()
                    main()

        mock_app.run_polling.assert_called_once()
