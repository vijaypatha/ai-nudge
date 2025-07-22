#!/bin/bash

# AI Nudge - Render Deployment Build Script
# This script handles the complete build process for Render deployment

set -e  # Exit on any error

echo "🚀 Starting AI Nudge build process for Render deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Build script must be run from the project root directory"
    exit 1
fi

print_status "Detecting deployment type..."

# Determine if this is a backend or frontend build based on environment
if [ "$RENDER_SERVICE_TYPE" = "web" ] || [ "$RENDER_SERVICE_TYPE" = "background_worker" ]; then
    BUILD_TYPE="backend"
    print_status "Detected backend build for service type: $RENDER_SERVICE_TYPE"
elif [ "$RENDER_SERVICE_TYPE" = "static_site" ]; then
    BUILD_TYPE="frontend"
    print_status "Detected frontend build for static site"
else
    # Default to backend if not specified
    BUILD_TYPE="backend"
    print_status "No service type specified, defaulting to backend build"
fi

# Backend build process
if [ "$BUILD_TYPE" = "backend" ]; then
    print_status "Starting backend build process..."
    
    # Navigate to backend directory
    cd backend
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed or not in PATH"
        exit 1
    fi
    
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p data
    
    # Set up environment variables if not already set
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # Run database migrations if needed
    print_status "Setting up database..."
    python -c "
import os
import sys
sys.path.append('.')
from data.database import engine, Base
from data.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
    
    print_success "Backend build completed successfully"
    
    # Return to root directory
    cd ..
    
    # Start the application
    print_status "Starting backend application..."
    exec uvicorn api.main:app --host 0.0.0.0 --port $PORT

# Frontend build process
elif [ "$BUILD_TYPE" = "frontend" ]; then
    print_status "Starting frontend build process..."
    
    # Navigate to frontend directory
    cd frontend
    
    # Check if Node.js is available
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed or not in PATH"
        exit 1
    fi
    
    # Check if npm is available
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed or not in PATH"
        exit 1
    fi
    
    print_status "Installing Node.js dependencies..."
    npm ci --only=production
    
    print_status "Building Next.js application..."
    npm run build
    
    print_success "Frontend build completed successfully"
    
    # Return to root directory
    cd ..
    
    # For static site deployment, the build output is ready
    print_status "Frontend build ready for deployment"
    exit 0

else
    print_error "Unknown build type: $BUILD_TYPE"
    exit 1
fi

print_success "Build process completed successfully!" 