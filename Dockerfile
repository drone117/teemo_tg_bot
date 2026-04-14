FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libfreetype-dev \
    libpng-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY src/ ./src/

# Create data directory for persistent storage
RUN mkdir -p /app/data

CMD ["python", "src/app.py"]
