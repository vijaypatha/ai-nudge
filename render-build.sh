#!/usr/bin/env bash

# AI Nudge - Render Build Script
# FINAL VERSION: Includes database migration step for safe deployments.

# exit on error
set -o errexit

echo "🚀 Starting AI Nudge build for Render..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0;33[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_status "Installing Python dependencies..."
pip install -r backend/requirements.txt
print_success "Dependencies installed."

# --- THIS IS THE CRITICAL ADDITION ---
print_status "Applying database migrations..."
alembic upgrade head
print_success "Database migrations applied successfully."
# ------------------------------------

print_status "Setting up Python path..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# Start the application using Gunicorn for better process management
print_status "Starting backend application with Gunicorn..."
exec gunicorn backend.api.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT