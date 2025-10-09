# Use an official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (optional but useful for pyarrow, pandas, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip3 install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port (Cloud Run ignores this, but uvicorn needs it)
EXPOSE 8080


# Start command (using Uvicorn, production-ready)
CMD ["fastapi", "dev", "--host", "0.0.0.0", "--port", "8080"]
#CMD ["fastapi", "dev", "--host", "127.0.0.1", "--port", "8080"]
