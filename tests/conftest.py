"""Shared fixtures and configuration for all tests."""

import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

# Add project root to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def fresh_data_dir(monkeypatch):
    """Create an isolated data directory for a test."""
    unique_dir = Path(tempfile.mkdtemp(prefix=f"babybot_{uuid.uuid4().hex[:8]}_"))
    data_file = unique_dir / "status.json"

    # Use monkeypatch to properly patch module attributes
    import src.data_manager as dm
    monkeypatch.setattr(dm, "DATA_DIR", unique_dir)
    monkeypatch.setattr(dm, "DATA_FILE", data_file)
    monkeypatch.setattr(dm, "ACTIVITIES_DATA_FILE", unique_dir / "activities.json")

    yield unique_dir

    # Cleanup
    import shutil
    shutil.rmtree(unique_dir, ignore_errors=True)


@pytest.fixture
def sample_user_status():
    """Create sample user status data."""
    return {
        "feeding": "Fed",
        "feeding_time": "2026-04-14 10:30:00",
        "sleeping": "Sleeping",
        "sleeping_time": "2026-04-14 09:15:00",
        "woke_up": "Fresh",
        "woke_up_time": "2026-04-14 08:00:00",
        "history": [
            {
                "action": "feeding",
                "status": "Fed",
                "time": "2026-04-14 10:30:00",
                "emoji": "🍼",
                "label": "Feeding"
            },
            {
                "action": "sleeping",
                "status": "Sleeping",
                "time": "2026-04-14 09:15:00",
                "emoji": "😴",
                "label": "Sleeping"
            },
            {
                "action": "woke_up",
                "status": "Fresh",
                "time": "2026-04-14 08:00:00",
                "emoji": "🌅",
                "label": "Woke up"
            }
        ],
        "last_updated": "2026-04-14 10:30:00"
    }


@pytest.fixture
def mock_query():
    """Create a mock callback query."""
    from unittest.mock import AsyncMock
    query = AsyncMock()
    query.from_user.id = 123
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.message = AsyncMock()
    query.message.reply_photo = AsyncMock()
    query.message.chat_id = 123
    return query


@pytest.fixture
def mock_update_message():
    """Create a mock update object for messages."""
    from unittest.mock import MagicMock, AsyncMock
    update = MagicMock()
    update.message = MagicMock()
    update.message.from_user.id = 123
    update.message.first_name = "TestUser"
    update.message.chat_id = 123
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock context."""
    from unittest.mock import MagicMock
    return MagicMock()
