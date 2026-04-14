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
        # Mock load_status to ensure clean state
        call_count = 0
        original_load = load_status
        def mock_load():
            return {}
        monkeypatch.setattr("src.data_manager.load_status", mock_load)
        
        update_user_status(1002, "feeding", "Fed")
        update_user_status(1002, "sleeping", "Sleeping")

        result = get_user_status(1002)
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
