FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install system dependencies (already present)
# ...

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (already present)
# ...

# Copy application code
COPY . .

# Run the worker
CMD ["python", "playwright_scraper/runner.py"]