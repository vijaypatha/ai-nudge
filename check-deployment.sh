#!/bin/bash

# AI Nudge - Deployment Status Checker
# This script checks the health and status of deployed services

set -e

echo "🔍 Checking AI Nudge deployment status..."

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

# Check if required tools are available
check_tools() {
    print_status "Checking required tools..."
    
    if command -v curl &> /dev/null; then
        print_success "curl is available"
    else
        print_error "curl is not installed"
        exit 1
    fi
    
    if command -v jq &> /dev/null; then
        print_success "jq is available"
    else
        print_warning "jq is not installed (JSON parsing will be limited)"
    fi
}

# Function to check service health
check_service() {
    local service_name=$1
    local service_url=$2
    local expected_status=${3:-200}
    
    print_status "Checking $service_name at $service_url"
    
    if curl -s -o /dev/null -w "%{http_code}" "$service_url" | grep -q "$expected_status"; then
        print_success "$service_name is healthy (HTTP $expected_status)"
        return 0
    else
        print_error "$service_name is not responding correctly"
        return 1
    fi
}

# Function to check environment variables
check_env_vars() {
    print_status "Checking environment variables..."
    
    # List of required environment variables
    local required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "JWT_SECRET_KEY"
        "OPENAI_API_KEY"
        "TWILIO_ACCOUNT_SID"
        "TWILIO_AUTH_TOKEN"
        "GOOGLE_CLIENT_ID"
        "GOOGLE_CLIENT_SECRET"
        "NEXT_PUBLIC_API_URL"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_success "All required environment variables are set"
    else
        print_warning "Missing environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
    fi
}

# Function to check database connectivity
check_database() {
    print_status "Checking database connectivity..."
    
    if [ -n "$DATABASE_URL" ]; then
        # Try to connect to database (this is a basic check)
        if python3 -c "
import os
import sys
sys.path.append('backend')
from data.database import engine
try:
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
            print_success "Database connection is working"
        else
            print_error "Database connection failed"
        fi
    else
        print_warning "DATABASE_URL not set, skipping database check"
    fi
}

# Function to check Redis connectivity
check_redis() {
    print_status "Checking Redis connectivity..."
    
    if [ -n "$REDIS_URL" ]; then
        if python3 -c "
import os
import redis
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
" 2>/dev/null; then
            print_success "Redis connection is working"
        else
            print_error "Redis connection failed"
        fi
    else
        print_warning "REDIS_URL not set, skipping Redis check"
    fi
}

# Function to check API endpoints
check_api_endpoints() {
    local base_url=${NEXT_PUBLIC_API_URL:-"http://localhost:8001"}
    
    print_status "Checking API endpoints..."
    
    # Health check endpoint
    if check_service "API Health" "$base_url/health" 200; then
        print_success "API health endpoint is responding"
    fi
    
    # Documentation endpoint
    if check_service "API Docs" "$base_url/docs" 200; then
        print_success "API documentation is accessible"
    fi
}

# Function to check frontend
check_frontend() {
    local frontend_url=${NEXT_PUBLIC_FRONTEND_URL:-"http://localhost:3000"}
    
    print_status "Checking frontend..."
    
    if check_service "Frontend" "$frontend_url" 200; then
        print_success "Frontend is accessible"
    fi
}

# Main execution
main() {
    echo "🚀 AI Nudge Deployment Status Checker"
    echo "====================================="
    echo ""
    
    # Check tools
    check_tools
    echo ""
    
    # Check environment variables
    check_env_vars
    echo ""
    
    # Check database
    check_database
    echo ""
    
    # Check Redis
    check_redis
    echo ""
    
    # Check API endpoints
    check_api_endpoints
    echo ""
    
    # Check frontend
    check_frontend
    echo ""
    
    print_status "Deployment status check completed!"
    echo ""
    print_status "Next steps:"
    echo "1. Review any warnings or errors above"
    echo "2. Check service logs if issues are found"
    echo "3. Verify all environment variables are set"
    echo "4. Test application functionality"
}

# Run main function
main "$@" 