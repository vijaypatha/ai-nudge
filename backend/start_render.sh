#!/bin/bash
set -e

echo "=== STARTING RENDER DEPLOYMENT ==="

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Check database state
echo "=== DATABASE STATE CHECK ==="
python -c "
from sqlmodel import Session, select
from data.database import engine
from data.models import User

session = Session(engine)
users = session.exec(select(User)).all()
print(f'Found {len(users)} users in database')
for user in users:
    print(f'- {user.full_name} ({user.email})')

if len(users) == 0:
    print('Database is empty - will run seeding')
    exit(1)
else:
    print('Database has data - skipping seed')
    exit(0)
"

# If database is empty, run seeding
if [ $? -eq 1 ]; then
    echo "=== DATABASE IS EMPTY - RUNNING SEED ==="
    
    # Try to create super user (may fail if env vars missing)
    echo "Attempting to create super user..."
    python create_super_user.py || echo "⚠️  Super user creation failed, continuing with seed data..."
    
    # Test imports first
    echo "Testing Python imports..."
    python -c "
import sys
print('Python version:', sys.version)
print('Testing imports...')
try:
    import asyncio
    print('✓ asyncio imported')
    from data.seed import seed_database
    print('✓ seed_database imported')
    print('✓ All imports successful')
except Exception as e:
    print('❌ Import error:', str(e))
    import traceback
    traceback.print_exc()
    exit(1)
"
    
    # Run seed database with error handling
    echo "Running database seeding..."
    python -c "
import asyncio
import sys
try:
    from data.seed import seed_database
    print('Starting seed_database()...')
    asyncio.run(seed_database())
    print('✓ Seed database completed successfully')
except Exception as e:
    print('❌ Seed database error:', str(e))
    import traceback
    traceback.print_exc()
    exit(1)
"
    
    echo "=== SEEDING COMPLETED ==="
else
    echo "=== DATABASE HAS DATA - SKIPPING SEED ==="
fi

# Start the server
echo "=== STARTING SERVER ==="
exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} 