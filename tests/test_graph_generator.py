"""Tests for src/graph_generator.py module."""

from src.graph_generator import generate_schedule_graph


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

    def test_generate_graph_returns_buffer(self, fresh_data_dir, sample_user_status):
        """Test that graph generation returns a bytes buffer."""
        result = generate_schedule_graph(sample_user_status)

        assert result is not None
        assert hasattr(result, "read")
        # Verify it's a valid PNG
        header = result.read(8)
        assert header[:4] == b'\x89PNG'

    def test_generate_graph_with_multiple_actions(self):
        """Test generating graph with multiple action types."""
        history = [
            {"action": "feeding", "status": "Fed", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Feeding"},
            {"action": "sleeping", "status": "Sleeping", "time": "2026-04-14 09:00:00", "emoji": "😴", "label": "Sleeping"},
            {"action": "woke_up", "status": "Fresh", "time": "2026-04-14 10:00:00", "emoji": "🌅", "label": "Woke up"},
        ]

        result = generate_schedule_graph({"history": history})
        assert result is not None

        # Verify the buffer contains PNG data
        result.seek(0)
        header = result.read(8)
        assert header[:4] == b'\x89PNG'

    def test_generate_graph_feeding_only(self):
        """Test generating graph with only feeding history."""
        history = [
            {"action": "feeding", "status": "Fed", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Feeding"},
        ]

        result = generate_schedule_graph({"history": history})
        assert result is not None

    def test_generate_graph_mixed_valid_invalid_dates(self):
        """Test generating graph with mix of valid and invalid dates."""
        history = [
            {"action": "feeding", "status": "Fed", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Feeding"},
            {"action": "feeding", "status": "Hungry", "time": "bad-date", "emoji": "🍼", "label": "Feeding"},
            {"action": "sleeping", "status": "Sleeping", "time": "2026-04-14 09:00:00", "emoji": "😴", "label": "Sleeping"},
        ]

        result = generate_schedule_graph({"history": history})
        assert result is not None

    def test_generate_graph_multiple_points_same_action(self):
        """Test generating graph with multiple points for same action type."""
        history = [
            {"action": "feeding", "status": "Fed", "time": "2026-04-14 08:00:00", "emoji": "🍼", "label": "Feeding"},
            {"action": "feeding", "status": "Hungry", "time": "2026-04-14 12:00:00", "emoji": "🍼", "label": "Feeding"},
            {"action": "feeding", "status": "Fed", "time": "2026-04-14 18:00:00", "emoji": "🍼", "label": "Feeding"},
        ]

        result = generate_schedule_graph({"history": history})
        assert result is not None

        result.seek(0)
        header = result.read(8)
        assert header[:4] == b'\x89PNG'
