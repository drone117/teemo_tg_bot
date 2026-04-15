"""Modern styling constants for baby activity graphs."""

# Modern color palette - soft, visually appealing colors with good contrast
ACTION_COLORS = {
    "feeding": "#FF9F43",      # Warm orange - soft but visible
    "sleeping": "#54A0FF",     # Calming blue - softer than pure blue
    "woke_up": "#1DD1A1",      # Fresh green - softer than pure green
}

# Background colors
BACKGROUND_COLOR = "#F8F9FA"    # Very light gray, modern clean look
AXIS_BACKGROUND = "#FFFFFF"     # Pure white for plot area
GRID_COLOR = "#E9ECEF"          # Subtle grid lines

# Text colors
TEXT_COLOR = "#2D3436"          # Dark gray for main text (softer than black)
TITLE_COLOR = "#2D3436"         # Dark gray for titles
SUBTITLE_COLOR = "#636E72"      # Medium gray for subtitles

# Desktop Typography settings
TITLE_FONT_SIZE = 16
TITLE_FONT_WEIGHT = "bold"
LABEL_FONT_SIZE = 12
TICK_FONT_SIZE = 10
LEGEND_FONT_SIZE = 11

# Desktop Layout settings (landscape orientation)
FIGURE_WIDTH = 14
FIGURE_HEIGHT = 6
MARGIN_TOP = 0.95
MARGIN_BOTTOM = 0.15
MARGIN_LEFT = 0.08
MARGIN_RIGHT = 0.95

# Mobile-specific settings (portrait orientation)
MOBILE_FIGURE_WIDTH = 8        # Narrower for mobile screens
MOBILE_FIGURE_HEIGHT = 10      # Taller for mobile portrait mode
MOBILE_TITLE_FONT_SIZE = 14    # Slightly smaller title
MOBILE_LABEL_FONT_SIZE = 11    # Slightly smaller labels
MOBILE_TICK_FONT_SIZE = 9      # Smaller tick labels
MOBILE_LEGEND_FONT_SIZE = 10   # Smaller legend text
MOBILE_MARGIN_TOP = 0.92       # More top margin for mobile
MOBILE_MARGIN_BOTTOM = 0.12    # More bottom margin for mobile
MOBILE_MARGIN_LEFT = 0.12      # More left margin for longer labels
MOBILE_MARGIN_RIGHT = 0.92     # More right margin for mobile
MOBILE_BAR_HEIGHT = 0.5        # Thinner bars for mobile
MOBILE_DURATION_LABEL_SIZE = 8 # Smaller duration labels for mobile

# Output settings
DESKTOP_DPI = 200              # High quality for desktop
MOBILE_DPI = 150               # Optimized DPI for mobile (file size vs quality)
MOBILE_OUTPUT_DPI = 120        # Further optimized for mobile data usage

# Bar styling
BAR_HEIGHT = 0.6
BAR_EDGE_COLOR = "white"
BAR_EDGE_WIDTH = 2
BAR_ALPHA = 0.8

# Duration label styling
DURATION_LABEL_SIZE = 9
DURATION_LABEL_COLOR = "#2D3436"
DURATION_LABEL_FONT_WEIGHT = "normal"

# Emoji labels for y-axis
ACTION_EMOJIS = {
    "feeding": "🍼",
    "sleeping": "😴",
    "woke_up": "🌅"
}

ACTION_LABELS = {
    "feeding": "Кормление",
    "sleeping": "Сон",
    "woke_up": "Проснулся"
}

# Mobile emoji labels (shorter text)
MOBILE_ACTION_LABELS = {
    "feeding": "Еда",
    "sleeping": "Сон",
    "woke_up": "Бодр."
}

# Y-axis positions (top to bottom)
Y_POSITIONS = {
    "feeding": 3,
    "sleeping": 2,
    "woke_up": 1
}

# Time formatting
TIME_FORMAT_SHORT = "%H:%M"      # For tick labels (e.g., "14:30")
TIME_FORMAT_LONG = "%m/%d %H:%M" # For longer ranges (e.g., "04/15 14:30")
DATE_FORMAT = "%d %b"            # For dates (e.g., "15 апр")

# Grid styling
GRIDLineStyle = "--"
GRID_ALPHA = 0.4
GRID_ZORDER = 1

# Marker styling (for points when duration can't be shown)
MARKER_SIZE = 100
MARKER_EDGE_COLOR = "white"
MARKER_EDGE_WIDTH = 2
MARKER_ZORDER = 5

# Line styling (for connecting points)
LINE_ALPHA = 0.3
LINE_WIDTH = 2
LINE_ZORDER = 3

# Duration bar styling
DURATION_BAR_ZORDER = 4
DURATION_BAR_ALPHA = 0.85