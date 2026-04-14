# Telegram Baby Bot

A simple Telegram bot to track baby care activities (feeding and sleeping status) with per-user tracking.

## Features

- **🍼 Feeding Tracker**: Cycles through `Hungry → Fed → Burping`
- **😴 Sleeping Tracker**: Cycles through `Awake → Sleeping → Deep Sleep`
- **🌅 Woke Up Tracker**: Cycles through `Just Woke Up → Fresh → Active`
- **📊 Statistics View**: Shows update counts and recent history log
- **📈 Schedule Graph**: Visual timeline graph of baby's sleep and feeding schedule
- **Per-User Tracking**: Each user has their own independent status
- **Timestamps**: Shows when status was last updated
- **Inline Buttons**: Easy status updates without typing commands
- **Error Handling**: Graceful error logging and recovery

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Show the status menu with inline buttons |
| `/help` | Display available commands |
| `/status` | View current status without buttons |

## Setup

### Prerequisites

- Docker and Docker Compose
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### Configuration

1. Clone or copy the project to your machine
2. Edit the `.env` file and add your bot token:
   ```env
   TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
   ```

### Running with Docker Compose

```bash
docker-compose up -d
```

### Running Locally

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export TELEGRAM_BOT_TOKEN=your_actual_bot_token_here

# Run the bot
python bot.py
```

## Data Storage

Status data is stored in `data/status.json` with per-user tracking:

```json
{
  "123456789": {
    "feeding": "Fed",
    "feeding_time": "2026-04-14 10:30:00",
    "sleeping": "Sleeping",
    "sleeping_time": "2026-04-14 09:15:00",
    "woke_up": "Fresh",
    "woke_up_time": "2026-04-14 08:00:00",
    "last_updated": "2026-04-14 10:30:00",
    "history": [
      {
        "action": "feeding",
        "status": "Fed",
        "time": "2026-04-14 10:30:00",
        "emoji": "🍼",
        "label": "Feeding"
      }
    ]
  }
}
```

The `data/` directory is persisted via Docker volume mapping.

## Project Structure

```
tg_baby_bot/
├── bot.py              # Main bot application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container definition
├── docker-compose.yml  # Docker orchestration
├── .env               # Environment variables (DO NOT COMMIT)
├── .gitignore         # Git ignore rules
└── data/              # Persistent storage for status
```

## Dependencies

- Python 3.12
- python-telegram-bot 21.10
- matplotlib 3.9.0
- Pillow 10.4.0

## Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=bot

## Security

- **Never commit your `.env` file** - it's listed in `.gitignore` for a reason
- If your bot token is exposed, revoke it immediately via [@BotFather](https://t.me/BotFather)

## License

MIT
