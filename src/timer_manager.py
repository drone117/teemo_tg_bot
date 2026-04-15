"""Intelligent activity timer management for baby care tracking."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Optional, List
import logging

from src.data_manager import load_user_activities, save_user_activities
from src.duration_calculator import format_duration_russian

logger = logging.getLogger(__name__)

# Set Moscow timezone
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

# Activity types with better names
ACTIVITIES = {
    "feed": {
        "emoji": "🍼",
        "name": "Кормление",
        "name_short": "Еда",
        "typical_duration": timedelta(minutes=20),  # 20 minutes typical feeding
        "min_duration": timedelta(minutes=10),
        "max_duration": timedelta(minutes=45)
    },
    "sleep": {
        "emoji": "😴",
        "name": "Сон",
        "name_short": "Сон",
        "typical_duration": timedelta(hours=2),  # 2 hours typical nap
        "min_duration": timedelta(minutes=30),
        "max_duration": timedelta(hours=4)
    },
    "wake": {
        "emoji": "🌅",
        "name": "Бодрствование",
        "name_short": "Бодр.",
        "typical_duration": timedelta(hours=2),  # 2 hours typical awake time
        "min_duration": timedelta(minutes=30),
        "max_duration": timedelta(hours=4)
    }
}

# Activity sequences (what naturally follows what)
NATURAL_SEQUENCES = {
    "feed": ["sleep", "wake"],   # After feeding, baby typically sleeps or stays awake
    "sleep": ["feed", "wake"],   # After sleep, baby typically eats or plays
    "wake": ["feed", "sleep"]    # When awake, baby typically eats or eventually sleeps
}


class ActivityTimer:
    """Represents a single activity with timer functionality."""

    def __init__(self, activity_type: str):
        self.activity_type = activity_type
        self.start_time = None
        self.end_time = None
        self.is_running = False

    def start(self):
        """Start the activity timer."""
        self.start_time = datetime.now(MOSCOW_TZ)
        self.end_time = None
        self.is_running = True

    def stop(self):
        """Stop the activity timer."""
        if self.is_running:
            self.end_time = datetime.now(MOSCOW_TZ)
            self.is_running = False

    @property
    def duration(self) -> Optional[timedelta]:
        """Get current duration of the activity."""
        if not self.start_time:
            return timedelta(0)

        end = self.end_time if self.end_time else datetime.now(MOSCOW_TZ)
        return end - self.start_time

    @property
    def is_completed(self) -> bool:
        """Check if activity is completed (stopped)."""
        return self.start_time is not None and not self.is_running

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "type": self.activity_type,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
            "duration_minutes": int(self.duration.total_seconds() / 60),
            "is_running": self.is_running
        }


class BabyScheduleManager:
    """Manages baby activity schedule with intelligent predictions."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.current_activity: Optional[ActivityTimer] = None
        self.activity_history: List[ActivityTimer] = []
        self._load_from_disk()

    def _load_from_disk(self):
        """Load saved activity history from disk."""
        saved = load_user_activities(self.user_id)

        for entry in saved.get("completed_activities", []):
            timer = ActivityTimer(entry["type"])
            timer.start_time = datetime.strptime(entry["start_time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=MOSCOW_TZ)
            if entry.get("end_time"):
                timer.end_time = datetime.strptime(entry["end_time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=MOSCOW_TZ)
            timer.is_running = False
            self.activity_history.append(timer)

        current = saved.get("current_activity")
        if current and current.get("is_running"):
            timer = ActivityTimer(current["type"])
            timer.start_time = datetime.strptime(current["start_time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=MOSCOW_TZ)
            timer.is_running = True
            self.current_activity = timer

    def _save_to_disk(self):
        """Persist current state to disk."""
        data = {
            "completed_activities": [a.to_dict() for a in self.activity_history],
            "current_activity": self.current_activity.to_dict() if self.current_activity else None,
        }
        save_user_activities(self.user_id, data)

    def start_activity(self, activity_type: str) -> Dict:
        """Start a new activity, automatically stopping any current activity."""
        # Stop current activity if running
        if self.current_activity and self.current_activity.is_running:
            self.current_activity.stop()
            self.activity_history.append(self.current_activity)

        # Start new activity
        self.current_activity = ActivityTimer(activity_type)
        self.current_activity.start()
        self._save_to_disk()

        return self.get_status_summary()

    def stop_current_activity(self) -> Dict:
        """Stop the current activity."""
        if self.current_activity and self.current_activity.is_running:
            self.current_activity.stop()
            self.activity_history.append(self.current_activity)
            self.current_activity = None
            self._save_to_disk()

        return self.get_status_summary()

    def get_status_summary(self) -> Dict:
        """Get comprehensive status summary."""
        if not self.current_activity:
            return {
                "status": "idle",
                "message": "Нет активного занятия",
                "current_activity": None,
                "suggestions": self._get_suggestions_for_idle()
            }

        activity_info = ACTIVITIES[self.current_activity.activity_type]
        duration = self.current_activity.duration

        # Determine if activity is within typical range
        is_within_typical = activity_info["min_duration"] <= duration <= activity_info["max_duration"]
        is_overdue = duration > activity_info["max_duration"]

        return {
            "status": "active",
            "current_activity": {
                "type": self.current_activity.activity_type,
                "emoji": activity_info["emoji"],
                "name": activity_info["name"],
                "start_time": self.current_activity.start_time.strftime("%H:%M"),
                "duration_minutes": int(duration.total_seconds() / 60),
                "duration_str": format_duration_russian(duration),
                "is_running": self.current_activity.is_running,
                "is_within_typical": is_within_typical,
                "is_overdue": is_overdue
            },
            "suggestions": self._get_suggestions_for_activity()
        }

    def _get_suggestions_for_idle(self) -> List[str]:
        """Get suggestions for when no activity is active."""
        if not self.activity_history:
            return ["Начните отслеживание, нажав кнопку начала занятия"]

        # Get last completed activity
        last_activity = self.activity_history[-1]
        time_since = datetime.now(MOSCOW_TZ) - last_activity.end_time

        if time_since < timedelta(minutes=30):
            # Recently ended activity - suggest continuation or rest
            activity_name = ACTIVITIES[last_activity.activity_type]["name"]
            return [f"После {activity_name} дайте ребенку отдых"]

        # Suggest based on time patterns
        suggestions = []
        for activity_type, info in ACTIVITIES.items():
            suggestions.append(f"Начните {info['name']}")

        return suggestions

    def _get_suggestions_for_activity(self) -> List[str]:
        """Get intelligent suggestions based on current activity."""
        if not self.current_activity:
            return []

        activity_type = self.current_activity.activity_type
        duration = self.current_activity.duration
        activity_info = ACTIVITIES[activity_type]

        suggestions = []

        # Time-based suggestions
        if duration < activity_info["min_duration"]:
            remaining = activity_info["min_duration"] - duration
            suggestions.append(f"Продолжайте еще {format_duration_russian(remaining)}")
        elif duration > activity_info["max_duration"]:
            suggestions.append(f"Занятие длится дольше обычного")
            # Suggest next logical activities
            next_activities = NATURAL_SEQUENCES.get(activity_type, [])
            for next_act in next_activities[:2]:  # Top 2 suggestions
                next_info = ACTIVITIES[next_act]
                suggestions.append(f"Рекомендуется: {next_info['name']}")
        else:
            # Within typical range
            suggestions.append(f"Все идет нормально! Продолжайте.")

        return suggestions

    def get_statistics_summary(self) -> Dict:
        """Get comprehensive statistics summary."""
        if not self.activity_history:
            return {
                "total_activities": 0,
                "message": "История пуста. Начните отслеживание!",
                "today_summary": None
            }

        # Calculate today's statistics
        today = datetime.now(MOSCOW_TZ).date()
        today_activities = [
            act for act in self.activity_history
            if act.start_time and act.start_time.date() == today
        ]

        if not today_activities:
            return {
                "total_activities": len(self.activity_history),
                "message": "Сегодня еще нет записей",
                "today_summary": None
            }

        # Calculate totals by activity type
        totals = {act_type: {"count": 0, "total_minutes": 0} for act_type in ACTIVITIES}

        for activity in today_activities:
            if activity.is_completed:
                totals[activity.activity_type]["count"] += 1
                totals[activity.activity_type]["total_minutes"] += int(activity.duration.total_seconds() / 60)

        # Format summary
        summary_lines = []
        for act_type, info in ACTIVITIES.items():
            stats = totals[act_type]
            if stats["count"] > 0:
                avg_duration = stats["total_minutes"] // stats["count"]
                summary_lines.append(f"{info['emoji']} {info['name']}: {stats['count']} раз, в среднем {avg_duration} мин")

        return {
            "total_activities": len(self.activity_history),
            "today_summary": summary_lines,
            "today_date": today.strftime("%d.%m.%Y"),
            "activity_breakdown": {
                act_type: {
                    "name": info["name"],
                    "emoji": info["emoji"],
                    "count": totals[act_type]["count"],
                    "total_minutes": totals[act_type]["total_minutes"],
                    "total_str": format_duration_russian(timedelta(minutes=totals[act_type]["total_minutes"]))
                }
                for act_type, info in ACTIVITIES.items()
            }
        }

    def get_simple_status_text(self) -> str:
        """Get simple, clean status text for display."""
        status = self.get_status_summary()

        if status["status"] == "idle":
            return "😴 Нет активного занятия"

        current = status["current_activity"]
        return f"{current['emoji']} {current['name']}: {current['duration_str']}"

    def get_activity_buttons(self) -> List[List[Dict]]:
        """Get simplified button layout."""
        if not self.current_activity or not self.current_activity.is_running:
            # No activity running - show start buttons
            return [
                [{"text": "🍼 Начать кормление", "callback_data": "start_feed"}],
                [{"text": "😴 Начать сон", "callback_data": "start_sleep"}],
                [{"text": "🌅 Начать бодрствование", "callback_data": "start_wake"}],
                [{"text": "📊 Статистика", "callback_data": "statistics"}]
            ]
        else:
            # Activity running - show stop button
            current_type = self.current_activity.activity_type
            activity_info = ACTIVITIES[current_type]

            return [
                [{"text": f"⏹️ Остановить {activity_info['name_short']}", "callback_data": "stop_current"}],
                [{"text": f"⏱️ {activity_info['emoji']} {activity_info['name']}: {format_duration_russian(self.current_activity.duration)}", "callback_data": "current_status"}],
                [{"text": "📊 Статистика", "callback_data": "statistics"}]
            ]