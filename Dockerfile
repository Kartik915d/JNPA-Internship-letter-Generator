FROM python:3.10-slim

# --------------------------------------------------
# Install system dependencies required by WeasyPrint
# --------------------------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Set working directory
# --------------------------------------------------
WORKDIR /app

# --------------------------------------------------
# Install Python dependencies
# --------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------
# Copy application code
# --------------------------------------------------
COPY . .

# --------------------------------------------------
# Expose port (Railway uses 8080)
# --------------------------------------------------
EXPOSE 8080

# --------------------------------------------------
# Start Flask app with Gunicorn
# --------------------------------------------------
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
