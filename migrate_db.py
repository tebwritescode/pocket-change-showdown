#!/usr/bin/env python3

"""
Database migration script for PCS Tracker v2.1.0
Adds reimbursement tracking and dashboard customization features.

Run this script to migrate existing databases to the new schema.
"""

import os
import sys
import sqlite3
from datetime import datetime

def migrate_database(db_path):
    """Migrate the database to the new schema"""
    print(f"Migrating database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    # Create backup
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup: {backup_path}")
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("Backup created successfully")
    except Exception as e:
        print(f"Failed to create backup: {e}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Checking current database schema...")
        
        # Check if reimbursement columns already exist in expense table
        cursor.execute("PRAGMA table_info(expense)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'is_reimbursable' not in columns:
            migrations_needed.append('expense_reimbursement')
        
        # Check if dashboard_preset table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dashboard_preset'")
        if not cursor.fetchone():
            migrations_needed.append('dashboard_preset_table')
        
        # Check if homepage_config table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='homepage_config'")
        if not cursor.fetchone():
            migrations_needed.append('homepage_config_table')
        
        if not migrations_needed:
            print("Database is already up to date!")
            conn.close()
            return True
        
        print(f"Migrations needed: {', '.join(migrations_needed)}")
        
        # Apply migrations
        if 'expense_reimbursement' in migrations_needed:
            print("Adding reimbursement columns to expense table...")
            cursor.execute("""
                ALTER TABLE expense ADD COLUMN is_reimbursable BOOLEAN DEFAULT 0
            """)
            cursor.execute("""
                ALTER TABLE expense ADD COLUMN reimbursement_status VARCHAR(20) DEFAULT 'none'
            """)
            cursor.execute("""
                ALTER TABLE expense ADD COLUMN reimbursement_notes TEXT
            """)
            print("✓ Reimbursement columns added")
        
        if 'dashboard_preset_table' in migrations_needed:
            print("Creating dashboard_preset table...")
            cursor.execute("""
                CREATE TABLE dashboard_preset (
                    id INTEGER NOT NULL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    config TEXT NOT NULL,
                    filters TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create a default preset
            cursor.execute("""
                INSERT INTO dashboard_preset (name, is_default, config, filters) VALUES (
                    'Default Dashboard',
                    1,
                    '{"widgets": [{"type": "category-pie", "title": "Expenses by Category", "size": "medium"}, {"type": "trend-line", "title": "Spending Trend", "size": "large"}, {"type": "total-spent", "title": "Total Spent", "size": "small"}, {"type": "reimbursable-amount", "title": "Reimbursable Amount", "size": "small"}], "layout": "grid"}',
                    '{"period": "month"}'
                )
            """)
            print("✓ Dashboard preset table created with default preset")
        
        if 'homepage_config_table' in migrations_needed:
            print("Creating homepage_config table...")
            cursor.execute("""
                CREATE TABLE homepage_config (
                    id INTEGER NOT NULL PRIMARY KEY,
                    sections TEXT NOT NULL DEFAULT '{}',
                    hero_settings TEXT DEFAULT '{}',
                    table_columns TEXT DEFAULT '{}',
                    widget_layout VARCHAR(20) DEFAULT '2-column',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create default homepage config
            cursor.execute("""
                INSERT INTO homepage_config (sections, hero_settings, table_columns, widget_layout) VALUES (
                    '{"hero": {"visible": true, "order": 1}, "stats": {"visible": true, "order": 2}, "recent_expenses": {"visible": true, "order": 3}, "quick_actions": {"visible": true, "order": 4}, "tips": {"visible": true, "order": 5}}',
                    '{"title": "Pocket Change Showdown", "subtitle": "Track every penny of your PCS move expenses", "show_logo": true}',
                    '{"recent_expenses": ["date", "title", "category", "amount", "reimbursable"]}',
                    '2-column'
                )
            """)
            print("✓ Homepage config table created with defaults")
        
        # Commit all changes
        conn.commit()
        print("✓ All migrations completed successfully!")
        
        # Verify the migrations
        print("Verifying database integrity...")
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result and result[0] == 'ok':
            print("✓ Database integrity check passed")
        else:
            print("⚠ Database integrity check failed")
        
        conn.close()
        print(f"Migration completed successfully!")
        print(f"Backup saved as: {backup_path}")
        return True
        
    except sqlite3.Error as e:
        print(f"Database error during migration: {e}")
        print("Attempting to restore from backup...")
        try:
            shutil.copy2(backup_path, db_path)
            print("Database restored from backup")
        except Exception as restore_error:
            print(f"Failed to restore backup: {restore_error}")
        return False
    except Exception as e:
        print(f"Unexpected error during migration: {e}")
        return False

def main():
    print("PCS Tracker Database Migration v2.1.0")
    print("=====================================")
    
    # Default database path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_db_path = os.path.join(script_dir, 'data', 'pcs_tracker.db')
    
    # Allow custom database path as command line argument
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = default_db_path
    
    if not os.path.exists(os.path.dirname(db_path)):
        print(f"Database directory does not exist: {os.path.dirname(db_path)}")
        print("Creating directory...")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    if migrate_database(db_path):
        print("\n✅ Migration completed successfully!")
        print("You can now restart your PCS Tracker application.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()