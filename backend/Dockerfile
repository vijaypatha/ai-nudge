# Use a specific Python runtime as a parent image.
FROM python:3.11-slim-bookworm

# --- Environment Configuration ---
# Set environment variables for Python.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# This is a critical fix: Add the project root to the PYTHONPATH.
# It allows Python to find modules like 'common' from within the 'backend' directory.
ENV PYTHONPATH=/app

# --- Dependency Installation ---
# Set the initial working directory for copying files.
WORKDIR /app

# Install system dependencies required by your Python packages (e.g., psycopg2).
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

# Install the Rust toolchain, a specific requirement for your project's dependencies.
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy only the requirements file first to leverage Docker layer caching.
COPY backend/requirements-render.txt .
# Install Python dependencies.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-render.txt

# --- Application Setup ---
# Copy the rest of your application code into the container.
COPY . .

# Create a non-root user for security and set correct file permissions.
# This helps prevent the "Permission denied" errors.
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chmod -R 755 /app

# Create the start script that will run migrations and then the web server.
# This script is owned by the 'app' user and has execute permissions.
RUN echo '#!/bin/bash\nset -e\necho "Running migrations..."\nalembic upgrade head\necho "Starting server..."\nexec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}' > /app/start.sh && \
    chmod +x /app/start.sh && \
    chown app:app /app/start.sh

# This is the final critical fix: Set the WORKDIR to the backend directory.
# This ensures all commands in the start script run from the correct location, fixing the Alembic error.
WORKDIR /app/backend

# Switch to the non-root user.
USER app

# Expose the port the app will run on.
EXPOSE 8000

# Set the default command to run when the container starts.
CMD ["/app/start.sh"]