#!/bin/bash

# Simple build script for Render deployment
set -e

echo "🚀 Starting simple build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

# Create necessary directories
mkdir -p backend/logs
mkdir -p backend/data

echo "✅ Build completed successfully!"

# Start the application
echo "Starting application..."
cd backend && uvicorn api.main:app --host 0.0.0.0 --port $PORT 