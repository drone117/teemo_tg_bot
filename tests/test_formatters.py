"""Tests for src/formatters.py module."""

from src.formatters import format_status, format_statistics


class TestFormatStatus:
    """Tests for format_status function."""

    def test_format_status_with_data(self, sample_user_status):
        """Test formatting status with data."""
        result = format_status(sample_user_status)

        assert "🍼 Feeding: Fed" in result
        assert "😴 Sleeping: Sleeping" in result
        assert "🌅 Woke up: Fresh" in result
        assert "2026-04-14 10:30:00" in result

    def test_format_status_with_unknown(self):
        """Test formatting status with unknown values."""
        user_status = {
            "feeding": "Unknown",
            "feeding_time": "Never",
            "sleeping": "Unknown",
            "sleeping_time": "Never",
            "woke_up": "Unknown",
            "woke_up_time": "Never",
            "last_updated": "Never"
        }
        result = format_status(user_status)

        assert "Unknown" in result
        assert "Never" in result

    def test_format_status_contains_all_fields(self):
        """Test that formatted output contains all expected fields."""
        user_status = {
            "feeding": "Fed",
            "feeding_time": "10:00",
            "sleeping": "Awake",
            "sleeping_time": "11:00",
            "woke_up": "Fresh",
            "woke_up_time": "08:00",
            "last_updated": "12:00"
        }
        result = format_status(user_status)

        assert "🍼 Feeding:" in result
        assert "🕒" in result
        assert "😴 Sleeping:" in result
        assert "🌅 Woke up:" in result
        assert "📝 Last updated:" in result


class TestFormatStatistics:
    """Tests for format_statistics function."""

    def test_format_statistics_no_history(self):
        """Test formatting statistics with no history."""
        user_status = {"history": []}
        result = format_statistics(user_status)

        assert "No statistics available" in result

    def test_format_statistics_counts(self, sample_user_status):
        """Test that statistics correctly counts actions."""
        result = format_statistics(sample_user_status)

        assert "🍼 Feeding updates: 1" in result
        assert "😴 Sleeping updates: 1" in result
        assert "🌅 Woke up updates: 1" in result
        assert "📝 Total updates: 3" in result

    def test_format_statistics_shows_recent(self, sample_user_status):
        """Test that statistics shows recent history."""
        result = format_statistics(sample_user_status)

        assert "Recent History" in result
        assert "🍼 Feeding: Fed" in result

    def test_format_statistics_limited_to_10(self):
        """Test that recent history is limited to 10 entries."""
        history = []
        for i in range(15):
            history.append({
                "action": "feeding",
                "status": f"Status{i}",
                "time": f"2026-04-14 0{i//10}:{i%10*6:02d}:00",
                "emoji": "🍼",
                "label": "Feeding"
            })

        user_status = {"history": history}
        result = format_statistics(user_status)

        # Count how many history entries are shown (should be 10, excluding summary line)
        lines = result.split("\n")
        history_lines = [l for l in lines if "🍼 Feeding: Status" in l]
        assert len(history_lines) == 10

    def test_format_statistics_reverse_chronological(self):
        """Test that recent history is shown in reverse chronological order."""
        history = [
            {"action": "feeding", "status": "First", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Feeding"},
            {"action": "feeding", "status": "Second", "time": "2026-04-14 09:00:00", "emoji": "🍼", "label": "Feeding"},
            {"action": "feeding", "status": "Third", "time": "2026-04-14 10:00:00", "emoji": "🍼", "label": "Feeding"},
        ]

        user_status = {"history": history}
        result = format_statistics(user_status)

        third_pos = result.find("Third")
        second_pos = result.find("Second")
        first_pos = result.find("First")

        assert third_pos < second_pos < first_pos

    def test_format_statistics_markdown_formatting(self, sample_user_status):
        """Test that statistics uses markdown formatting."""
        result = format_statistics(sample_user_status)

        assert "*📊 Statistics Summary*" in result
        assert "*Recent History (last 10):*" in result
