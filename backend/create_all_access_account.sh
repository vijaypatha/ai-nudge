#!/bin/bash

# Create the All-Access Standard Account
# This script runs the database migration and creates the special user account.

set -e

echo "🚀 Deploying All-Access Standard Account"
echo "========================================"

# Step 1: Run database migration
echo "📦 Running database migration..."
source venv/bin/activate
python -m alembic upgrade head

# Step 2: Create the user account
# The python script will now read details from your .env file
echo "👤 Creating the user account..."
python backend/create_super_user.py

echo ""
echo "✅ Deployment complete!"
echo "If no errors occurred, the account was created successfully."
echo ""