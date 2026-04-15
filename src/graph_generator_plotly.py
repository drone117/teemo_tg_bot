"""Modern timeline graph generation using Plotly for better mobile optimization and emoji support."""

import io
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Tuple, Optional

import plotly.graph_objects as go
import plotly.io as pio

logger = logging.getLogger(__name__)

from src.graph_styles import (
    ACTION_COLORS, BACKGROUND_COLOR, AXIS_BACKGROUND, GRID_COLOR,
    TEXT_COLOR, Y_POSITIONS,
)
from src.duration_calculator import format_duration_russian, parse_history_time

# Set Moscow timezone
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

# Configure Plotly defaults for mobile
pio.templates.default = "plotly_white"
pio.renderers.default = "png"

# Mobile-optimized default settings
DEFAULT_MOBILE_CONFIG = {
    'displayModeBar': False,
    'responsive': True,
    'staticPlot': True  # Disable interactivity for static images
}

def calculate_sleep_periods(history: List[Dict]) -> List[Tuple[datetime, datetime]]:
    """Calculate sleep periods from history.

    Args:
        history: List of history entries

    Returns:
        List of (start_time, end_time) tuples for sleep periods
    """
    sleep_periods = []
    current_sleep_start = None

    for entry in history:
        try:
            entry_time = parse_history_time(entry["time"])

            if entry["action"] == "sleeping" and entry["status"] in ["Спит", "Глубокий сон"]:
                if current_sleep_start is None:
                    current_sleep_start = entry_time
            elif entry["action"] == "woke_up" and current_sleep_start:
                # Sleep ended
                sleep_periods.append((current_sleep_start, entry_time))
                current_sleep_start = None
        except (ValueError, KeyError):
            continue

    # Handle case where baby is currently sleeping
    if current_sleep_start:
        current_time = datetime.now(MOSCOW_TZ)
        sleep_periods.append((current_sleep_start, current_time))

    return sleep_periods


def calculate_feeding_periods(history: List[Dict]) -> List[Tuple[datetime, datetime]]:
    """Calculate feeding periods from history.

    Since feeding is instantaneous, we create short periods around each feeding time
    for visualization purposes.

    Args:
        history: List of history entries

    Returns:
        List of (start_time, end_time) tuples for feeding periods
    """
    feeding_periods = []

    for entry in history:
        try:
            if entry["action"] == "feeding":
                feeding_time = parse_history_time(entry["time"])
                # Create a 15-minute window around feeding time for visualization
                feeding_periods.append((feeding_time - timedelta(minutes=7), feeding_time + timedelta(minutes=8)))
        except (ValueError, KeyError):
            continue

    return feeding_periods


def calculate_awake_periods(history: List[Dict]) -> List[Tuple[datetime, datetime]]:
    """Calculate awake periods from history.

    Args:
        history: List of history entries

    Returns:
        List of (start_time, end_time) tuples for awake periods
    """
    awake_periods = []
    current_awake_start = None

    for entry in history:
        try:
            entry_time = parse_history_time(entry["time"])

            if entry["action"] == "woke_up":
                current_awake_start = entry_time
            elif entry["action"] == "sleeping" and entry["status"] in ["Спит", "Глубокий сон"] and current_awake_start:
                # Awake period ended
                awake_periods.append((current_awake_start, entry_time))
                current_awake_start = None
        except (ValueError, KeyError):
            continue

    # Handle case where baby is currently awake
    if current_awake_start:
        current_time = datetime.now(MOSCOW_TZ)
        awake_periods.append((current_awake_start, current_time))

    return awake_periods


def create_timeline_traces(sleep_periods, feeding_periods, awake_periods, mobile=True):
    """Create Plotly traces for the timeline.

    Args:
        sleep_periods: List of (start, end) tuples for sleep
        feeding_periods: List of (start, end) tuples for feeding
        awake_periods: List of (start, end) tuples for awake time
        mobile: Whether to optimize for mobile

    Returns:
        List of Plotly scatter traces
    """
    traces = []

    # Mobile label settings
    if mobile:
        label_sleep = "😴 Сон"
        label_feeding = "🍼 Еда"
        label_awake = "🌅 Бодр."
        bar_width = 0.7
        text_font_size = 11
        title_font_size = 16
    else:
        label_sleep = "😴 Сон"
        label_feeding = "🍼 Кормление"
        label_awake = "🌅 Проснулся"
        bar_width = 0.8
        text_font_size = 12
        title_font_size = 18

    # Helper function to create traces with dots at start/end and connecting lines
    def create_bar_trace(periods, y_position, color, name, label_prefix):
        if not periods:
            return None

        # Prepare line segments (start -> end) with NaN separators
        line_xs, line_ys = [], []
        # Prepare dot markers at start and end points
        dot_xs, dot_ys, dot_hover = [], [], []
        # Prepare duration text labels at center of each segment
        text_xs, text_ys, text_labels = [], [], []

        for start, end in periods:
            duration = end - start
            duration_str = format_duration_russian(duration)
            center = start + (end - start) / 2
            time_range = f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
            hover_text = f"{label_prefix}<br>{time_range}<br>Длительность: {duration_str}"

            # Connecting line (start -> end only)
            line_xs.extend([start, end, None])
            line_ys.extend([y_position, y_position, None])

            # Dots at start and end
            dot_xs.extend([start, end])
            dot_ys.extend([y_position, y_position])
            dot_hover.extend([hover_text, hover_text])

            # Duration label at center
            text_xs.append(center)
            text_ys.append(y_position)
            text_labels.append(duration_str)

        # Line trace connecting start and end of each period
        traces.append(go.Scatter(
            x=line_xs, y=line_ys,
            mode='lines',
            line=dict(color=color, width=6 if mobile else 8),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Dot markers at start and end points
        traces.append(go.Scatter(
            x=dot_xs, y=dot_ys,
            mode='markers',
            name=name,
            marker=dict(
                size=10 if mobile else 12,
                color=color,
                line=dict(color='white', width=2)
            ),
            hovertext=dot_hover,
            hoverinfo='text',
            showlegend=True
        ))

        # Duration text below each line
        traces.append(go.Scatter(
            x=text_xs, y=[y - 0.3 for y in text_ys],
            mode='text',
            text=text_labels,
            textfont=dict(size=text_font_size - 1, color="#636E72"),
            textposition='top center',
            showlegend=False,
            hoverinfo='skip'
        ))

        return True

    # Create traces for each activity type
    create_bar_trace(sleep_periods, 2, ACTION_COLORS['sleeping'], label_sleep, "😴 Сон")
    create_bar_trace(awake_periods, 1, ACTION_COLORS['woke_up'], label_awake, "🌅 Бодрствует")
    create_bar_trace(feeding_periods, 3, ACTION_COLORS['feeding'], label_feeding, "🍼 Кормление")

    return traces


def generate_schedule_graph_plotly(user_status: Dict, mobile: bool = True) -> Optional[io.BytesIO]:
    """Generate a modern timeline graph using Plotly.

    Args:
        user_status: Dict containing user's status with 'history' key.
        mobile: If True, optimize for mobile devices (portrait orientation).

    Returns:
        BytesIO buffer containing PNG image, or None if no valid data.
    """
    history = user_status.get("history", [])

    if not history:
        return None

    # Calculate time periods for each activity
    sleep_periods = calculate_sleep_periods(history)
    feeding_periods = calculate_feeding_periods(history)
    awake_periods = calculate_awake_periods(history)

    if not (sleep_periods or feeding_periods or awake_periods):
        return None

    # Get all periods for time range calculation
    all_periods = []
    for start, end in sleep_periods:
        all_periods.append(('sleeping', start, end))
    for start, end in awake_periods:
        all_periods.append(('woke_up', start, end))
    for start, end in feeding_periods:
        all_periods.append(('feeding', start, end))

    # Sort by start time
    all_periods.sort(key=lambda x: x[1])

    # Calculate time range with padding
    min_time = min(period[1] for period in all_periods)
    max_time = max(period[2] for period in all_periods)
    time_range = (max_time - min_time).total_seconds()

    if time_range == 0:
        padding = timedelta(hours=1)
    else:
        padding = timedelta(seconds=time_range * 0.1)

    # Mobile-optimized dimensions
    if mobile:
        width, height = 480, 800  # Portrait mobile dimensions
        margin_top = 80
        margin_bottom = 60
        margin_left = 60
        margin_right = 40
        font_size_title = 18
        font_size_axis = 12
        font_size_tick = 10
    else:
        width, height = 1000, 600  # Desktop dimensions
        margin_top = 80
        margin_bottom = 60
        margin_left = 80
        margin_right = 40
        font_size_title = 20
        font_size_axis = 14
        font_size_tick = 12

    # Create figure
    fig = go.Figure()

    # Add traces
    traces = create_timeline_traces(sleep_periods, feeding_periods, awake_periods, mobile)
    for trace in traces:
        fig.add_trace(trace)

    # Update layout for mobile optimization
    fig.update_layout(
        title=dict(
            text='📊 Временная шкала режима ребёнка',
            font=dict(size=font_size_title, color=TEXT_COLOR, family='Arial, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(
                text='Время (МСК)',
                font=dict(size=font_size_axis, color=TEXT_COLOR)
            ),
            range=[min_time - padding, max_time + padding],
            tickfont=dict(size=font_size_tick, color=TEXT_COLOR),
            gridcolor=GRID_COLOR,
            showgrid=True,
            gridwidth=1,
            zeroline=False
        ),
        yaxis=dict(
            tickvals=[1, 2, 3],
            ticktext=['🌅 Бодр.' if mobile else '🌅 Проснулся',
                     '😴 Сон',
                     '🍼 Еда' if mobile else '🍼 Кормление'],
            tickfont=dict(size=font_size_tick + 2 if mobile else font_size_tick + 4, color=TEXT_COLOR),
            gridcolor=GRID_COLOR,
            showgrid=True,
            gridwidth=1,
            zeroline=False
        ),
        margin=dict(
            t=margin_top,
            b=margin_bottom,
            l=margin_left,
            r=margin_right
        ),
        plot_bgcolor=AXIS_BACKGROUND,
        paper_bgcolor=BACKGROUND_COLOR,
        width=width,
        height=height,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=font_size_tick, color=TEXT_COLOR)
        ),
    )

    # Update x-axis format based on time range
    if time_range < 3600:  # Less than 1 hour
        tickformat = '%H:%M'
    elif time_range < 86400:  # Less than 1 day
        tickformat = '%H:%M'
    else:  # More than 1 day
        tickformat = '%d %b %H:%M'

    fig.update_xaxes(tickformat=tickformat)

    # Convert to image bytes
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=1.5)
        buf = io.BytesIO(img_bytes)
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return None


# Maintain backward compatibility
def generate_schedule_graph(user_status: Dict, mobile: bool = True) -> Optional[io.BytesIO]:
    """Generate a timeline graph - automatically uses Plotly implementation.

    Args:
        user_status: Dict containing user's status with 'history' key.
        mobile: If True, optimize for mobile devices.

    Returns:
        BytesIO buffer containing PNG image, or None if no valid data.
    """
    return generate_schedule_graph_plotly(user_status, mobile)