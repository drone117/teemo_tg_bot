"""Duration calculations and Russian time formatting for baby activities."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Set Moscow timezone
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def format_duration_russian(duration: Optional[timedelta]) -> str:
    """Format duration in Russian with proper plural forms.

    Args:
        duration: timedelta object or None

    Returns:
        Russian formatted duration string (e.g., "2ч 30мин", "1час 15мин")

    Examples:
        >>> format_duration_russian(timedelta(hours=2, minutes=30))
        "2ч 30мин"
        >>> format_duration_russian(timedelta(hours=1, minutes=15))
        "1час 15мин"
        >>> format_duration_russian(timedelta(minutes=45))
        "45мин"
    """
    if duration is None or duration.total_seconds() < 0:
        return "0мин"

    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    parts = []

    # Handle hours with proper Russian plural forms
    if hours > 0:
        if hours == 1:
            hours_text = f"{hours}час"
        elif 2 <= hours <= 4:
            hours_text = f"{hours}часа"
        else:
            hours_text = f"{hours}часов"
        parts.append(hours_text)

    # Handle minutes with proper Russian plural forms
    if minutes > 0:
        if minutes == 1:
            minutes_text = f"{minutes}минута"
        elif 2 <= minutes <= 4:
            minutes_text = f"{minutes}минуты"
        else:
            minutes_text = f"{minutes}минут"
        parts.append(minutes_text)

    return " ".join(parts) if parts else "0мин"


def parse_history_time(time_str: str) -> datetime:
    """Parse history time string to datetime object with Moscow timezone.

    Args:
        time_str: Time string in format "YYYY-MM-DD HH:MM:SS"

    Returns:
        datetime object with Moscow timezone
    """
    dt_naive = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    return dt_naive.replace(tzinfo=MOSCOW_TZ)


def calculate_sleep_duration(history: List[Dict]) -> Optional[Dict]:
    """Calculate sleep duration from "fell asleep" → "woke up" transitions.

    Args:
        history: List of history entries with action, status, time

    Returns:
        Dict with current_sleep_info or None:
        {
            'is_sleeping': bool,
            'duration': Optional[timedelta],
            'duration_str': str,  # Russian formatted
            'start_time': Optional[datetime],
            'end_time': Optional[datetime],
            'last_sleep_duration': Optional[timedelta],
            'last_sleep_duration_str': str
        }
    """
    if not history:
        return None

    # Find most recent sleep-related events
    sleep_events = [h for h in history if h["action"] == "sleeping"]
    if not sleep_events:
        return None

    most_recent_sleep = sleep_events[-1]
    sleep_start_time = parse_history_time(most_recent_sleep["time"])
    current_time = datetime.now(MOSCOW_TZ)

    # Check if currently sleeping (most recent status is a sleep state)
    sleep_statuses = ["Спит", "Глубокий сон"]
    is_sleeping = most_recent_sleep["status"] in sleep_statuses

    if is_sleeping:
        # Currently sleeping - calculate duration so far
        duration = current_time - sleep_start_time
        duration_str = format_duration_russian(duration)

        return {
            'is_sleeping': True,
            'duration': duration,
            'duration_str': duration_str,
            'start_time': sleep_start_time,
            'end_time': None,
            'last_sleep_duration': None,
            'last_sleep_duration_str': ''
        }

    # Not currently sleeping - find last completed sleep
    # Look for woke_up events after the most recent sleep event
    woke_up_events = [h for h in history if h["action"] == "woke_up"]

    for woke_up_event in reversed(woke_up_events):
        woke_up_time = parse_history_time(woke_up_event["time"])
        if woke_up_time > sleep_start_time:
            # Found the wake-up that ended this sleep
            duration = woke_up_time - sleep_start_time
            duration_str = format_duration_russian(duration)

            return {
                'is_sleeping': False,
                'duration': duration,
                'duration_str': duration_str,
                'start_time': sleep_start_time,
                'end_time': woke_up_time,
                'last_sleep_duration': duration,
                'last_sleep_duration_str': duration_str
            }

    # No wake-up found (shouldn't happen but handle gracefully)
    return None


def calculate_time_since_last_feeding(history: List[Dict]) -> Optional[Dict]:
    """Calculate time since last feeding.

    Args:
        history: List of history entries

    Returns:
        Dict with feeding timing info or None:
        {
            'last_feeding_time': datetime,
            'time_since': timedelta,
            'time_since_str': str,  # Russian formatted
            'last_feeding_status': str  # What feeding state they were in
        }
    """
    if not history:
        return None

    # Find most recent feeding event
    feeding_events = [h for h in history if h["action"] == "feeding"]
    if not feeding_events:
        return None

    most_recent_feeding = feeding_events[-1]
    feeding_time = parse_history_time(most_recent_feeding["time"])
    current_time = datetime.now(MOSCOW_TZ)

    time_since = current_time - feeding_time
    time_since_str = format_duration_russian(time_since)

    return {
        'last_feeding_time': feeding_time,
        'time_since': time_since,
        'time_since_str': time_since_str,
        'last_feeding_status': most_recent_feeding["status"]
    }


def calculate_awake_duration(history: List[Dict]) -> Optional[Dict]:
    """Calculate how long baby has been awake.

    Args:
        history: List of history entries

    Returns:
        Dict with awake duration info or None:
        {
            'duration': timedelta,
            'duration_str': str,  # Russian formatted
            'wake_time': datetime,
            'is_awake': bool
        }
    """
    if not history:
        return None

    # Find most recent woke_up event
    woke_up_events = [h for h in history if h["action"] == "woke_up"]
    if not woke_up_events:
        return None

    most_recent_wake = woke_up_events[-1]
    wake_time = parse_history_time(most_recent_wake["time"])
    current_time = datetime.now(MOSCOW_TZ)

    # Check if currently awake
    sleep_events = [h for h in history if h["action"] == "sleeping"]
    is_awake = True

    if sleep_events:
        most_recent_sleep = sleep_events[-1]
        sleep_time = parse_history_time(most_recent_sleep["time"])
        if sleep_time > wake_time:
            is_awake = False
            return {
                'duration': timedelta(0),
                'duration_str': "0мин",
                'wake_time': wake_time,
                'is_awake': False
            }

    if is_awake:
        duration = current_time - wake_time
        duration_str = format_duration_russian(duration)

        return {
            'duration': duration,
            'duration_str': duration_str,
            'wake_time': wake_time,
            'is_awake': True
        }

    return None


def calculate_daily_summary(history: List[Dict]) -> Dict:
    """Calculate daily activity summaries.

    Args:
        history: List of history entries

    Returns:
        Dict with daily statistics:
        {
            'today': {
                'feed_count': int,
                'total_sleep_hours': float,
                'total_sleep_str': str,
                'sleep_episodes': int,
                'avg_sleep_duration': str,
                'date': str  # YYYY-MM-DD
            },
            'yesterday': {...}  # Same structure for yesterday
        }
    """
    if not history:
        return {
            'today': {
                'feed_count': 0,
                'total_sleep_hours': 0.0,
                'total_sleep_str': '0ч',
                'sleep_episodes': 0,
                'avg_sleep_duration': '0мин',
                'date': datetime.now(MOSCOW_TZ).strftime('%Y-%m-%d')
            }
        }

    current_time = datetime.now(MOSCOW_TZ)
    today_date = current_time.date()
    yesterday_date = (current_time - timedelta(days=1)).date()

    # Initialize daily data
    daily_data = {
        today_date: {
            'feed_count': 0,
            'sleep_periods': [],  # List of sleep durations in minutes
            'sleep_episodes': 0,
            'date': today_date.strftime('%Y-%m-%d')
        },
        yesterday_date: {
            'feed_count': 0,
            'sleep_periods': [],
            'sleep_episodes': 0,
            'date': yesterday_date.strftime('%Y-%m-%d')
        }
    }

    # Track sleep periods
    current_sleep_start = None

    for entry in history:
        try:
            entry_time = parse_history_time(entry["time"])
            entry_date = entry_time.date()

            # Only process today and yesterday
            if entry_date not in [today_date, yesterday_date]:
                continue

            if entry_date not in daily_data:
                # If we have data from earlier days, add them
                daily_data[entry_date] = {
                    'feed_count': 0,
                    'sleep_periods': [],
                    'sleep_episodes': 0,
                    'date': entry_date.strftime('%Y-%m-%d')
                }

            daily_data[entry_date]['feed_count'] += 1

            # Track sleep periods
            if entry["action"] == "sleeping" and entry["status"] in ["Спит", "Глубокий сон"]:
                current_sleep_start = entry_time
            elif entry["action"] == "woke_up" and current_sleep_start:
                # Calculate sleep duration
                sleep_end = entry_time
                sleep_duration = sleep_end - current_sleep_start
                sleep_minutes = sleep_duration.total_seconds() / 60

                if sleep_end.date() == current_sleep_start.date():
                    # Sleep completely within one day
                    if sleep_end.date() in daily_data:
                        daily_data[sleep_end.date()]['sleep_periods'].append(sleep_minutes)
                        daily_data[sleep_end.date()]['sleep_episodes'] += 1
                else:
                    # Sleep spans midnight - split between days
                    midnight = sleep_end.replace(hour=0, minute=0, second=0, microsecond=0)
                    first_day_duration = midnight - current_sleep_start
                    second_day_duration = sleep_end - midnight

                    if current_sleep_start.date() in daily_data:
                        daily_data[current_sleep_start.date()]['sleep_periods'].append(
                            first_day_duration.total_seconds() / 60
                        )
                        daily_data[current_sleep_start.date()]['sleep_episodes'] += 1

                    if sleep_end.date() in daily_data:
                        daily_data[sleep_end.date()]['sleep_periods'].append(
                            second_day_duration.total_seconds() / 60
                        )
                        # Don't increment sleep_episodes for second day (continuation)

                current_sleep_start = None

        except (ValueError, KeyError) as e:
            logger.warning(f"Error processing history entry: {e}")
            continue

    # Calculate summaries for today and yesterday
    result = {}

    for date_key, date_str in [(today_date, 'today'), (yesterday_date, 'yesterday')]:
        if date_key in daily_data:
            day_data = daily_data[date_key]
            total_sleep_minutes = sum(day_data['sleep_periods'])
            total_sleep_hours = total_sleep_minutes / 60

            # Calculate average sleep duration
            if day_data['sleep_episodes'] > 0:
                avg_sleep_minutes = total_sleep_minutes / day_data['sleep_episodes']
                avg_sleep_str = format_duration_russian(timedelta(minutes=avg_sleep_minutes))
            else:
                avg_sleep_str = "0мин"

            result[date_str] = {
                'feed_count': day_data['feed_count'],
                'total_sleep_hours': round(total_sleep_hours, 1),
                'total_sleep_str': format_duration_russian(timedelta(minutes=total_sleep_minutes)),
                'sleep_episodes': day_data['sleep_episodes'],
                'avg_sleep_duration': avg_sleep_str,
                'date': day_data['date']
            }
        else:
            result[date_str] = {
                'feed_count': 0,
                'total_sleep_hours': 0.0,
                'total_sleep_str': '0ч',
                'sleep_episodes': 0,
                'avg_sleep_duration': '0мин',
                'date': date_key.strftime('%Y-%m-%d')
            }

    return result


def get_current_state_duration(history: List[Dict], action: str) -> Optional[Dict]:
    """Calculate how long the baby has been in the current state for a specific action.

    Args:
        history: List of history entries
        action: One of "feeding", "sleeping", "woke_up"

    Returns:
        Dict with duration info or None:
        {
            'duration': timedelta,
            'duration_str': str,
            'start_time': datetime,
            'current_status': str
        }
    """
    if not history:
        return None

    # Find most recent event for this action
    action_events = [h for h in history if h["action"] == action]
    if not action_events:
        return None

    most_recent = action_events[-1]
    start_time = parse_history_time(most_recent["time"])
    current_time = datetime.now(MOSCOW_TZ)

    duration = current_time - start_time
    duration_str = format_duration_russian(duration)

    return {
        'duration': duration,
        'duration_str': duration_str,
        'start_time': start_time,
        'current_status': most_recent['status']
    }