FROM python:3.13-slim

WORKDIR /app

# Install Google Chrome for kaleido (Plotly image rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    && wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y --no-install-recommends /tmp/google-chrome.deb \
    && rm -f /tmp/google-chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY src/ ./src/

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH=/app

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Use the timer-based system
CMD ["python", "src/app_timer.py"]
