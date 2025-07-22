#!/bin/bash

# AI Nudge - Vercel Deployment Script
# This script handles deployment to Vercel for both frontend and backend

set -e  # Exit on any error

echo "🚀 Starting AI Nudge Vercel deployment..."

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

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    print_error "Vercel CLI is not installed. Please install it first:"
    echo "npm install -g vercel"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Deployment script must be run from the project root directory"
    exit 1
fi

# Function to deploy frontend
deploy_frontend() {
    print_status "Deploying frontend to Vercel..."
    
    cd frontend
    
    # Check if vercel.json exists
    if [ ! -f "vercel.json" ]; then
        print_error "vercel.json not found in frontend directory"
        exit 1
    fi
    
    # Deploy to Vercel
    print_status "Running Vercel deployment for frontend..."
    vercel --prod --yes
    
    print_success "Frontend deployed successfully!"
    
    cd ..
}

# Function to deploy backend
deploy_backend() {
    print_status "Deploying backend to Vercel..."
    
    cd backend
    
    # Check if vercel.json exists
    if [ ! -f "deployment/vercel.json" ]; then
        print_error "vercel.json not found in backend/deployment directory"
        exit 1
    fi
    
    # Copy vercel.json to backend root
    cp deployment/vercel.json .
    
    # Deploy to Vercel
    print_status "Running Vercel deployment for backend..."
    vercel --prod --yes
    
    # Clean up
    rm vercel.json
    
    print_success "Backend deployed successfully!"
    
    cd ..
}

# Main deployment logic
print_status "Starting deployment process..."

# Check command line arguments
if [ "$1" = "frontend" ]; then
    deploy_frontend
elif [ "$1" = "backend" ]; then
    deploy_backend
elif [ "$1" = "all" ] || [ -z "$1" ]; then
    print_status "Deploying both frontend and backend..."
    deploy_frontend
    deploy_backend
else
    print_error "Invalid argument. Usage:"
    echo "  $0 [frontend|backend|all]"
    echo "  Default: all"
    exit 1
fi

print_success "Deployment completed successfully!"

# Display next steps
echo ""
print_status "Next steps:"
echo "1. Configure environment variables in Vercel dashboard"
echo "2. Set up custom domains if needed"
echo "3. Configure database connections"
echo "4. Test the deployed application"
echo ""
print_status "For environment variables, see DEPLOYMENT.md for the complete list" 