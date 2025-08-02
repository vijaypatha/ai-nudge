# Use a specific Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    pkg-config \
    curl \
    git \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements and install dependencies
COPY backend/requirements-render.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-render.txt

# Copy application code
COPY . .

# Create non-root user and set proper permissions
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chmod -R 755 /app

# Create start script with proper permissions
RUN echo '#!/bin/bash\nset -e\necho "Running migrations..."\nalembic upgrade head\necho "Starting server..."\nexec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}' > /app/start.sh && \
    chmod +x /app/start.sh && \
    chown app:app /app/start.sh

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Use start script
CMD ["/app/start.sh"]