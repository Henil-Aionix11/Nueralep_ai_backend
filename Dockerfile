ARG BASE_IMAGE=python
ARG BASE_IMAGE_TAG=3.12-slim

FROM $BASE_IMAGE:$BASE_IMAGE_TAG

# Install system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    make \
    procps \
    libpq-dev \
    gcc \
    python3-dev \
    build-essential \
    libffi-dev \
    sqlite3 \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data \
    /app/chroma_db \
    /app/logs \
    /app/docs \
    /app/uploads \
    /app/exported_documents \
    && chmod -R 777 /app/data \
    && chmod -R 777 /app/chroma_db \
    && chmod -R 777 /app/docs \
    && chmod -R 777 /app/uploads \
    && chmod -R 777 /app/exported_documents \
    && chmod -R 755 /app/logs

# Ensure directories have full permissions
RUN find /app/data -type d -exec chmod 777 {} \; \
    && find /app/chroma_db -type d -exec chmod 777 {} \; \
    && find /app/data -type f -exec chmod 666 {} \; 2>/dev/null || true \
    && find /app/chroma_db -type f -exec chmod 666 {} \; 2>/dev/null || true

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SQLALCHEMY_SILENCE_UBER_WARNING=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

# Run migrations and start application
CMD bash -c "echo ' Environment validation.....' && \
    if [ -z \"\$POSTGRES_DATABASE_HOST\" ] || [ -z \"\$POSTGRES_DATABASE_USERNAME\" ] || [ -z \"\$POSTGRES_DATABASE_PASSWORD\" ] || [ -z \"\$POSTGRES_DATABASE_NAME\" ]; then \
        echo \" ERROR: Required database environment variables are not set\"; \
        exit 1; \
    fi && \
    echo ' Running database migrations.....' && \
    python -m alembic upgrade head && \
    echo ' Migrations completed' && \
    echo ' Starting FastAPI application.....' && \
    python -m main"
