# Use the official Playwright Python image which includes browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium browser
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Set environment variable for headless mode (default to true in Docker)
ENV HEADLESS=true
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]
