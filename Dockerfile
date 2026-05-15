FROM python:3.10.12-slim

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /code

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /code

