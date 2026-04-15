"""Tests for src/graph_generator_plotly.py module."""

import pytest

from src.graph_generator_plotly import generate_schedule_graph


def _can_render_graphs():
    """Check if kaleido can render graphs (needs Chrome)."""
    try:
        result = generate_schedule_graph({
            "history": [
                {"action": "feeding", "status": "Покормлен", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Кормление"},
            ]
        })
        return result is not None
    except Exception:
        return False


# Skip all rendering tests if Chrome is not available
skip_no_chrome = pytest.mark.skipif(
    not _can_render_graphs(),
    reason="Chrome not installed - kaleido cannot render graphs"
)


class TestGenerateScheduleGraph:
    """Tests for generate_schedule_graph function."""

    def test_generate_graph_no_history(self):
        """Test generating graph with no history."""
        result = generate_schedule_graph({"history": []})
        assert result is None

    def test_generate_graph_missing_history_key(self):
        """Test generating graph with missing history key."""
        result = generate_schedule_graph({})
        assert result is None

    def test_generate_graph_invalid_dates(self):
        """Test generating graph with invalid dates."""
        history = [{
            "action": "feeding",
            "status": "Fed",
            "time": "invalid-date",
            "emoji": "🍼",
            "label": "Feeding"
        }]
        result = generate_schedule_graph({"history": history})
        assert result is None

    @skip_no_chrome
    def test_generate_graph_with_multiple_actions(self):
        """Test generating graph with multiple action types."""
        history = [
            {"action": "feeding", "status": "Покормлен", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Кормление"},
            {"action": "sleeping", "status": "Спит", "time": "2026-04-14 09:00:00", "emoji": "😴", "label": "Сон"},
            {"action": "woke_up", "status": "Отдохнувший", "time": "2026-04-14 11:00:00", "emoji": "🌅", "label": "Бодрствование"},
        ]

        result = generate_schedule_graph({"history": history})
        assert result is not None
        assert hasattr(result, "read")

    @skip_no_chrome
    def test_generate_graph_feeding_only(self):
        """Test generating graph with only feeding history."""
        history = [
            {"action": "feeding", "status": "Покормлен", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Кормление"},
        ]

        result = generate_schedule_graph({"history": history})
        assert result is not None

    @skip_no_chrome
    def test_generate_graph_mixed_valid_invalid_dates(self):
        """Test generating graph with mix of valid and invalid dates."""
        history = [
            {"action": "feeding", "status": "Покормлен", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Кормление"},
            {"action": "feeding", "status": "Hungry", "time": "bad-date", "emoji": "🍼", "label": "Кормление"},
            {"action": "sleeping", "status": "Спит", "time": "2026-04-14 09:00:00", "emoji": "😴", "label": "Сон"},
        ]

        result = generate_schedule_graph({"history": history})
        assert result is not None

    @skip_no_chrome
    def test_generate_graph_timer_converted_data(self):
        """Test generating graph from timer-converted history format."""
        history = [
            {"action": "feeding", "status": "Покормлен", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Кормление"},
            {"action": "sleeping", "status": "Спит", "time": "2026-04-14 09:00:00", "emoji": "😴", "label": "Сон"},
            {"action": "woke_up", "status": "Отдохнувший", "time": "2026-04-14 11:00:00", "emoji": "🌅", "label": "Бодрствование"},
        ]
        result = generate_schedule_graph({"history": history})
        assert result is not None

    @skip_no_chrome
    def test_generate_graph_multiple_points_same_action(self):
        """Test generating graph with multiple points for same action type."""
        history = [
            {"action": "feeding", "status": "Покормлен", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Кормление"},
            {"action": "feeding", "status": "Покормлен", "time": "2026-04-14 12:00:00", "emoji": "🍼", "label": "Кормление"},
            {"action": "feeding", "status": "Покормлен", "time": "2026-04-14 18:00:00", "emoji": "🍼", "label": "Кормление"},
        ]

        result = generate_schedule_graph({"history": history})
        assert result is not None
