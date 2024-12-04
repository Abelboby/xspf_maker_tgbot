# Directory structure:
# project_root/
# ├── Dockerfile
# ├── docker-compose.yml
# ├── requirements.txt
# ├── app.py
# ├── upload.py
# └── .env

# Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Command to run the application
CMD ["python", "app.py"]