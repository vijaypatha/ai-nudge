# backend/Dockerfile

# Use a specific Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

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
    && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain (required by some Python packages)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements file first to leverage Docker cache
COPY requirements-render.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-render.txt

# Copy application code
COPY . .

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Default command to run the application (will be overridden by Render's startCommand)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]