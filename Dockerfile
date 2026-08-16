FROM python:3.13-slim

WORKDIR /app

# Install system dependencies (needed for numpy/scipy compilation if wheels unavailable)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY config/ config/
COPY cli.py .

# Set Python path so imports work
ENV PYTHONPATH=/app

# Default: run the scan
CMD ["python", "src/scanner/run_scan.py"]
