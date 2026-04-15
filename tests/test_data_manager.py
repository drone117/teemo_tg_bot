"""Tests for src/data_manager.py module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.data_manager import (
    load_status,
    save_status,
    get_user_status,
    update_user_status,
    load_user_activities,
    save_user_activities,
    DEFAULT_USER_STATUS,
    HISTORY_LIMIT,
)


class TestLoadStatus:
    """Tests for load_status function."""

    def test_load_status_file_not_exists(self, fresh_data_dir):
        """Test loading when file doesn't exist."""
        result = load_status()
        assert result == {}

    def test_load_status_valid_json(self, fresh_data_dir, sample_user_status):
        """Test loading valid status file."""
        data_file = fresh_data_dir / "status.json"
        with open(data_file, "w") as f:
            json.dump({"123": sample_user_status}, f)

        result = load_status()
        assert "123" in result
        assert result["123"]["feeding"] == "Fed"

    def test_load_status_invalid_json(self, fresh_data_dir):
        """Test loading invalid JSON file."""
        data_file = fresh_data_dir / "status.json"
        with open(data_file, "w") as f:
            f.write("invalid json {{{")

        result = load_status()
        assert result == {}


class TestSaveStatus:
    """Tests for save_status function."""

    def test_save_status_creates_directory(self, fresh_data_dir):
        """Test that save_status creates directory if needed."""
        test_dir = fresh_data_dir / "subdir"
        test_file = test_dir / "status.json"

        with patch("src.data_manager.DATA_DIR", test_dir):
            with patch("src.data_manager.DATA_FILE", test_file):
                save_status({"test": "data"})

        assert test_file.exists()
        with open(test_file) as f:
            assert json.load(f) == {"test": "data"}

    def test_save_status_writes_data(self, fresh_data_dir, sample_user_status):
        """Test that save_status writes correct data."""
        save_status({"123": sample_user_status})

        data_file = fresh_data_dir / "status.json"
        assert data_file.exists()

        with open(data_file) as f:
            data = json.load(f)

        assert "123" in data
        assert data["123"]["feeding"] == "Fed"


class TestGetUserStatus:
    """Tests for get_user_status function."""

    def test_get_user_status_new_user(self, fresh_data_dir):
        """Test getting status for non-existent user."""
        result = get_user_status(999)

        assert result["feeding"] == "Unknown"
        assert result["feeding_time"] == "Never"
        assert result["sleeping"] == "Unknown"
        assert result["sleeping_time"] == "Never"
        assert result["woke_up"] == "Unknown"
        assert result["woke_up_time"] == "Never"
        assert result["history"] == []
        assert result["last_updated"] == "Never"

    def test_get_user_status_returns_copy(self, fresh_data_dir):
        """Test that get_user_status returns a copy, not a reference."""
        save_status({"123": dict(DEFAULT_USER_STATUS)})
        result1 = get_user_status(123)
        result1["feeding"] = "Modified"

        result2 = get_user_status(123)
        assert result2["feeding"] == "Unknown"

    def test_get_user_status_existing_user(self, fresh_data_dir, sample_user_status):
        """Test getting status for existing user."""
        save_status({"123": sample_user_status})
        result = get_user_status(123)

        assert result["feeding"] == "Fed"
        assert result["sleeping"] == "Sleeping"
        assert result["woke_up"] == "Fresh"
        assert len(result["history"]) == 3


class TestUpdateUserStatus:
    """Tests for update_user_status function."""

    def test_update_creates_user_if_not_exists(self, fresh_data_dir):
        """Test that update creates new user entry."""
        result = update_user_status(1001, "feeding", "Hungry")

        assert result["feeding"] == "Hungry"
        assert result["feeding_time"] != "Never"
        assert result["last_updated"] != "Never"
        assert len(result["history"]) == 1

    def test_update_adds_to_history(self, fresh_data_dir, monkeypatch):
        """Test that update adds entry to history."""
        # Use in-memory storage to track state - start completely fresh
        memory_store = {}

        def mock_load():
            return memory_store.copy()

        def mock_save(data):
            memory_store.clear()
            memory_store.update(data)

        monkeypatch.setattr("src.data_manager.load_status", mock_load)
        monkeypatch.setattr("src.data_manager.save_status", mock_save)

        # Use a unique user ID to avoid conflicts with other tests
        unique_user_id = 99999

        # Start with a fresh user to avoid any state from previous tests
        memory_store[str(unique_user_id)] = {
            "feeding": "Unknown",
            "feeding_time": "Never",
            "sleeping": "Unknown",
            "sleeping_time": "Never",
            "woke_up": "Unknown",
            "woke_up_time": "Never",
            "history": [],
            "last_updated": "Never"
        }

        update_user_status(unique_user_id, "feeding", "Fed")
        update_user_status(unique_user_id, "sleeping", "Sleeping")

        result = get_user_status(unique_user_id)
        assert len(result["history"]) == 2

    def test_update_limits_history_to_limit(self, fresh_data_dir):
        """Test that history is limited to HISTORY_LIMIT entries."""
        for i in range(HISTORY_LIMIT + 10):
            update_user_status(1003, "feeding", f"Status{i}")

        result = get_user_status(1003)
        assert len(result["history"]) == HISTORY_LIMIT

    def test_update_feeding_status(self, fresh_data_dir):
        """Test updating feeding status."""
        result = update_user_status(1004, "feeding", "Fed")

        assert result["feeding"] == "Fed"
        assert "feeding_time" in result
        assert result["history"][-1]["action"] == "feeding"
        assert result["history"][-1]["emoji"] == "🍼"

    def test_update_sleeping_status(self, fresh_data_dir):
        """Test updating sleeping status."""
        result = update_user_status(1005, "sleeping", "Sleeping")

        assert result["sleeping"] == "Sleeping"
        assert result["history"][-1]["emoji"] == "😴"

    def test_update_woke_up_status(self, fresh_data_dir):
        """Test updating woke up status."""
        result = update_user_status(1006, "woke_up", "Fresh")

        assert result["woke_up"] == "Fresh"
        assert result["history"][-1]["emoji"] == "🌅"

    def test_update_preserves_other_fields(self, fresh_data_dir, sample_user_status):
        """Test that updating one field preserves others."""
        save_status({"1007": sample_user_status})
        update_user_status(1007, "feeding", "Burping")

        result = get_user_status(1007)
        assert result["feeding"] == "Burping"
        assert result["sleeping"] == "Sleeping"
        assert result["woke_up"] == "Fresh"


class TestLoadUserActivities:
    """Tests for load_user_activities function."""

    def test_load_no_file(self, fresh_data_dir):
        """Test loading when file doesn't exist."""
        result = load_user_activities(123)
        assert result == {}

    def test_load_existing_user(self, fresh_data_dir):
        """Test loading existing user data."""
        save_user_activities(123, {"completed_activities": [], "current_activity": None})
        result = load_user_activities(123)
        assert "completed_activities" in result

    def test_load_nonexistent_user(self, fresh_data_dir):
        """Test loading nonexistent user returns empty."""
        save_user_activities(999, {"completed_activities": [], "current_activity": None})
        result = load_user_activities(888)
        assert result == {}


class TestSaveUserActivities:
    """Tests for save_user_activities function."""

    def test_save_creates_file(self, fresh_data_dir):
        """Test that save creates the activities file."""
        save_user_activities(456, {"completed_activities": [], "current_activity": None})
        activities_file = fresh_data_dir / "activities.json"
        assert activities_file.exists()

    def test_save_and_load_roundtrip(self, fresh_data_dir):
        """Test that saved data can be loaded back."""
        data = {
            "completed_activities": [
                {"type": "feed", "start_time": "2026-04-14 08:00:00", "end_time": "2026-04-14 08:20:00", "duration_minutes": 20, "is_running": False}
            ],
            "current_activity": None,
        }
        save_user_activities(789, data)
        result = load_user_activities(789)
        assert len(result["completed_activities"]) == 1
        assert result["completed_activities"][0]["type"] == "feed"

    def test_save_overwrites(self, fresh_data_dir):
        """Test that save overwrites previous data."""
        save_user_activities(111, {"completed_activities": [{"type": "feed"}], "current_activity": None})
        save_user_activities(111, {"completed_activities": [], "current_activity": None})
        result = load_user_activities(111)
        assert result["completed_activities"] == []
