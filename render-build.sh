#!/bin/bash

# AI Nudge - Render Build Script
# Simplified build script for Render deployment

set -e

echo "🚀 Starting AI Nudge build for Render..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: Build script must be run from the project root directory"
    exit 1
fi

print_status "Installing Python dependencies..."
pip install -r backend/requirements.txt

print_status "Creating necessary directories..."
mkdir -p backend/logs
mkdir -p backend/data

print_status "Setting up Python path..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

print_success "Backend build completed successfully!"

# Start the application
print_status "Starting backend application..."
exec uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT 