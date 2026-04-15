# Telegram Baby Bot

A Telegram bot for tracking baby care activities (feeding, sleeping, wake time) with per-user timer-based tracking and visual schedule graphs.

## Features

- **Timer-based tracking** — start/stop timers for each activity instead of confusing status cycles
- **Smart suggestions** — contextual tips based on activity duration and natural sequences
- **Visual schedule graph** — Plotly-powered timeline of baby's day (mobile-optimized)
- **Per-user tracking** — each user has independent activity history
- **Persistent storage** — activity data survives bot restarts
- **Inline keyboard** — simple tap-based interface, no typing needed

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Show status menu with activity buttons |
| `/help` | Display available commands and usage tips |
| `/status` | View current status without buttons |

## How It Works

The bot uses a simple **start/stop timer** model:

1. Press a button to start an activity (feeding, sleep, or wake time)
2. The bot shows a running timer with duration
3. Press stop when the activity ends
4. The bot suggests what to do next based on patterns

## Setup

### Prerequisites

- Docker and Docker Compose (or Python 3.13+)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### Running with Docker Compose

```bash
# Set your bot token in .env
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env

# Start
docker-compose up -d
```

### Running Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=your_token_here
python src/app_timer.py
```

## Data Storage

Activity data is stored in `data/` (gitignored):

- `data/activities.json` — timer-based activity history per user
- `data/status.json` — legacy status data (kept for backward compatibility)

The `data/` directory is persisted via Docker volume mapping.

## Project Structure

```
tg_baby_bot/
├── src/
│   ├── app_timer.py              # Bot entry point and app configuration
│   ├── timer_handlers.py         # Telegram command/callback handlers
│   ├── timer_manager.py          # Activity timer logic and smart suggestions
│   ├── data_manager.py           # JSON file persistence
│   ├── duration_calculator.py    # Russian time formatting utilities
│   ├── graph_generator_plotly.py # Timeline graph generation (Plotly)
│   └── graph_styles.py           # Graph color palette and layout constants
├── tests/                        # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pytest.ini
```

## Dependencies

- Python 3.13
- python-telegram-bot 21.10
- plotly >= 5.18
- kaleido >= 0.2.1 (image rendering)
- Pillow 10.4.0

## Testing

```bash
pytest -v
```

Note: graph rendering tests are skipped unless Chrome is available (required by kaleido).

## License

MIT
