# Use a specific Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies for common Python packages
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

# Install Rust toolchain (required by some Python packages like cryptography)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements file first to leverage Docker cache
COPY requirements-render.txt .

# Install Python dependencies globally (no virtual environment)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-render.txt

# Copy application code
COPY . .

# Create a non-root user for security (optional but recommended)
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Use a shell command to run migrations and start the app
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]