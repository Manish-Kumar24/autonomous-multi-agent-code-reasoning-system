# Use official Python image
FROM python:3.11-slim

# Install git (fixes your Railway error)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8080

# Start app
CMD uvicorn main:app --host 0.0.0.0 --port $PORT