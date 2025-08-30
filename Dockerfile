# Multi-architecture Dockerfile for PCS Tracker
FROM --platform=$TARGETPLATFORM python:3.11-slim

# Build arguments for multi-arch support
ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG TARGETOS
ARG TARGETARCH

# Set working directory
WORKDIR /app

# Install system dependencies - need g++ for pandas on ARM
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY pdf_utils.py .
COPY db_init.py .
COPY templates/ templates/
COPY static/ static/

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/uploads

# Create non-root user for security
RUN useradd -m -u 1000 pcsuser && \
    chown -R pcsuser:pcsuser /app && \
    chmod 755 /app/data /app/uploads

# Switch to non-root user
USER pcsuser

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/')" || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "app:app"]