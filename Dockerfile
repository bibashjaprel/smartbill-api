# BillSmart API Dockerfile for Render deployment
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Remove any old .venv and __pycache__ to avoid stale builds
RUN rm -rf .venv && find . -type d -name "__pycache__" -exec rm -rf {} +

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "start_server.py"]
