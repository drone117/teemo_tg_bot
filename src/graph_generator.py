"""Graph generation module for visualizing baby schedule timeline."""

import io
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# Configuration for each action type
Y_POSITIONS = {"feeding": 3, "sleeping": 2, "woke_up": 1}
ACTION_COLORS = {"feeding": "#FF9800", "sleeping": "#2196F3", "woke_up": "#4CAF50"}
ACTION_LABELS = {"feeding": "Feeding", "sleeping": "Sleeping", "woke_up": "Woke Up"}


def generate_schedule_graph(user_status):
    """Generate a timeline graph of baby's schedule.

    Args:
        user_status: Dict containing user's status with 'history' key.

    Returns:
        BytesIO buffer containing PNG image, or None if no valid data.
    """
    history = user_status.get("history", [])

    if not history:
        return None

    # Parse history into datetime objects
    feeding_times = []
    sleeping_times = []
    woke_up_times = []

    for entry in history:
        try:
            dt = datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")
            if entry["action"] == "feeding":
                feeding_times.append(dt)
            elif entry["action"] == "sleeping":
                sleeping_times.append(dt)
            elif entry["action"] == "woke_up":
                woke_up_times.append(dt)
        except ValueError:
            continue

    if not (feeding_times or sleeping_times or woke_up_times):
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor('#f0f0f0')
    ax.set_facecolor('#ffffff')

    # Plot each category
    for action, times in [
        ("feeding", feeding_times),
        ("sleeping", sleeping_times),
        ("woke_up", woke_up_times),
    ]:
        if times:
            y_values = [Y_POSITIONS[action]] * len(times)
            ax.scatter(
                times, y_values,
                c=ACTION_COLORS[action],
                s=100, zorder=5,
                label=ACTION_LABELS[action],
                edgecolors='white',
                linewidth=1.5,
            )

            # Connect points with lines
            if len(times) > 1:
                ax.plot(times, y_values, c=ACTION_COLORS[action], alpha=0.3, linewidth=2)

    # Formatting
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(['🌅 Woke Up', '😴 Sleeping', '🍼 Feeding'])
    ax.set_ylim(0.5, 3.5)
    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_title('Baby Schedule Timeline', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', framealpha=0.9)

    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.xticks(rotation=45, ha='right')

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Adjust layout
    plt.tight_layout()

    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf
