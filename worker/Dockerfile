# worker/Dockerfile
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

# --- THIS IS THE FIX ---
# Run the worker as a module (-m) so relative imports work.
# This tells Python to run the 'runner' module inside the 'playwright_scraper' package.
CMD ["python", "-m", "playwright_scraper.runner"]