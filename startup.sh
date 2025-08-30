#!/bin/bash

# Run database initialization as a single process
echo "Initializing database..."
python -c "
from app import app, db
from db_init import run_auto_migration, initialize_database

# Run migration
print('Running database migration...')
if run_auto_migration():
    print('Database migration completed successfully')
else:
    print('Warning: Database migration encountered issues')

# Initialize database
with app.app_context():
    db.create_all()
    initialize_database(app, db)
    print('Database initialization complete')
"

# Check if initialization was successful
if [ $? -eq 0 ]; then
    echo "Database initialization successful, starting application..."
    # Start gunicorn without running the initialization again
    exec gunicorn --bind 0.0.0.0:5001 --workers 4 --timeout 120 app:app
else
    echo "Database initialization failed!"
    exit 1
fi