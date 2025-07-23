# File: backend/run_migrations.py

import logging
from data.database import create_db_and_tables
from data.seed import seed_database # Assuming seed_database is in backend/data/seed.py

# Set up basic logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    logging.info("--- Running database migrations and seeding ---")
    
    # This calls the function from your database.py file
    create_db_and_tables()
    
    # This calls your seeding function
    seed_database()
    
    logging.info("--- Migrations and seeding complete ---")