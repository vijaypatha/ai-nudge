#!/bin/bash

# Create the All-Access Standard Account (Docker Version)
# This script runs the database migration and creates the special user account using Docker.

set -e

echo "🚀 Deploying All-Access Standard Account (Docker)"
echo "=================================================="

# Step 1: Run database migration using Docker
echo "📦 Running database migration..."
docker-compose exec backend python -m alembic upgrade head

# Step 2: Create the user account using Docker
# The python script will now read details from the environment variables
echo "👤 Creating the user account..."
docker-compose exec backend python create_super_user.py

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔐 You can now log in with the phone number defined in your environment variables!"
echo ""