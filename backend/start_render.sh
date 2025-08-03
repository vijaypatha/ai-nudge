#!/bin/bash

set -e

echo "=== STARTING RENDER DEPLOYMENT ==="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."
    alembic upgrade head
    log "✅ Database migrations completed"
}

# Function to check if database needs seeding
check_database_state() {
    log "=== DATABASE STATE CHECK ==="
    
    # Use current directory instead of /tmp for better permissions
    local db_check_file="./db_check_result"
    
    python -c "
import sys
try:
    from sqlmodel import Session, select
    from data.database import engine
    from data.models import User
    
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        user_count = len(users)
        print(f'Found {user_count} users in database')
        
        if user_count == 0:
            print('NEEDS_SEEDING=true')
            print('Database is empty - will run seeding')
        else:
            print('NEEDS_SEEDING=false')
            print('Database has data - skipping seed')
            for user in users:
                print(f'- {user.full_name} ({user.email})')
                
except Exception as e:
    print(f'Database check error: {str(e)}')
    import traceback
    traceback.print_exc()
    print('NEEDS_SEEDING=true')
    print('Database check failed - will run seeding')
" > "$db_check_file" 2>&1

    # Check if file was created and grep with error handling
    if [ -f "$db_check_file" ] && grep -q "NEEDS_SEEDING=true" "$db_check_file" 2>/dev/null; then
        # Cleanup temp file
        rm -f "$db_check_file"
        return 0  # Needs seeding (success for if condition)
    else
        # Cleanup temp file
        rm -f "$db_check_file"
        return 1  # Has data (failure for if condition)
    fi
}

# Function to create superuser
create_superuser() {
    log "Attempting to create super user..."
    if [ -f "create_super_user.py" ]; then
        python create_super_user.py || {
            log "⚠️ Super user creation failed or skipped (may already exist)"
        }
    else
        log "⚠️ create_super_user.py not found, skipping"
    fi
}

# Function to run database seeding
run_database_seeding() {
    log "=== DATABASE IS EMPTY - RUNNING SEED ==="
    
    # Test imports first
    log "Testing Python imports..."
    python -c "
import sys
print('Python version:', sys.version)
print('Testing imports...')
try:
    import asyncio
    print('✓ asyncio imported')
    from data.seed import seed_database
    print('✓ seed_database imported from data.seed')
    print('✓ All imports successful')
except Exception as e:
    print('❌ Import error:', str(e))
    import traceback
    traceback.print_exc()
    # Do not exit - let the server start anyway
"
    
    # Run seed database with error handling
    log "Running database seeding..."
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
    # Do not exit - let the server start anyway
"
    
    log "=== SEEDING COMPLETED ==="
}

# Function to start the application server
start_server() {
    log "=== STARTING SERVER ==="
    exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
}

# Main execution flow
main() {
    log "Initializing production deployment..."
    
    # Step 1: Run migrations
    run_migrations
    
    # Step 2: Check if database needs seeding
    if check_database_state; then
        log "Database is empty - proceeding with initialization"
        
        # Step 3a: Create superuser
        create_superuser
        
        # Step 3b: Run database seeding
        run_database_seeding
    else
        log "=== DATABASE HAS DATA - SKIPPING SEED ==="
    fi
    
    # Step 4: Start the server (this should ALWAYS happen)
    start_server
}

# Execute main function
main "$@"
