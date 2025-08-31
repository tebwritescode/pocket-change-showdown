#!/usr/bin/env python3

"""
Database initialization and migration handler for PCS Tracker.
Automatically runs on application startup to ensure database is up-to-date.
"""

import os
import sqlite3
from datetime import datetime
import shutil

# Current application version
CURRENT_VERSION = "2.1.1"

# Migration history - maps versions to their required migrations
MIGRATION_HISTORY = {
    "2.0.0": [],  # Base version
    "2.1.0": ["reimbursement_tracking", "dashboard_preset", "homepage_config", "version_tracking"]
}

def ensure_database_directory():
    """Ensure the data directory exists"""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        print(f"Creating data directory: {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_database_version(cursor):
    """Get the current database version from settings table"""
    try:
        cursor.execute("SELECT db_version FROM settings LIMIT 1")
        result = cursor.fetchone()
        if result:
            return result[0]
    except sqlite3.Error:
        pass
    return "2.0.0"  # Default to 2.0.0 if no version found

def update_database_version(cursor, version):
    """Update the database version in settings table"""
    try:
        cursor.execute("UPDATE settings SET db_version = ?, app_version = ? WHERE id = 1", (version, version))
    except sqlite3.Error:
        # If settings table doesn't have version columns, add them
        try:
            cursor.execute("ALTER TABLE settings ADD COLUMN db_version VARCHAR(20) DEFAULT '2.0.0'")
            cursor.execute("ALTER TABLE settings ADD COLUMN app_version VARCHAR(20) DEFAULT '2.1.0'")
            cursor.execute("UPDATE settings SET db_version = ?, app_version = ? WHERE id = 1", (version, version))
        except sqlite3.Error:
            pass

def check_and_migrate_database(db_path):
    """Check database schema and apply migrations if needed"""
    
    # If database doesn't exist, it will be created by SQLAlchemy
    if not os.path.exists(db_path):
        print(f"Database will be created at: {db_path}")
        return True
    
    print(f"Checking database schema at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current database version
        current_db_version = get_database_version(cursor)
        print(f"Current database version: {current_db_version}")
        print(f"Target application version: {CURRENT_VERSION}")
        
        if current_db_version == CURRENT_VERSION:
            print("✅ Database is already up to date")
            conn.close()
            return True
        
        # Check if reimbursement columns exist in expense table
        cursor.execute("PRAGMA table_info(expense)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrations_applied = []
        
        # Check and apply reimbursement fields migration
        if 'is_reimbursable' not in columns:
            print("Applying migration: Adding reimbursement tracking fields...")
            
            # Create backup before migration
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            print(f"Backup created: {backup_path}")
            
            try:
                cursor.execute("ALTER TABLE expense ADD COLUMN is_reimbursable BOOLEAN DEFAULT 0")
                cursor.execute("ALTER TABLE expense ADD COLUMN reimbursement_status VARCHAR(20) DEFAULT 'none'")
                cursor.execute("ALTER TABLE expense ADD COLUMN reimbursement_notes TEXT")
                conn.commit()
                migrations_applied.append("reimbursement_tracking")
                print("✓ Reimbursement tracking fields added")
            except sqlite3.Error as e:
                print(f"Migration error: {e}")
                conn.rollback()
        
        # Check if dashboard_preset table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dashboard_preset'")
        if not cursor.fetchone():
            print("Applying migration: Creating dashboard preset table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_preset (
                    id INTEGER NOT NULL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    config TEXT NOT NULL,
                    filters TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create default preset
            cursor.execute("""
                INSERT INTO dashboard_preset (name, is_default, config, filters) VALUES (
                    'Default Dashboard',
                    1,
                    '{"widgets": [{"type": "category-pie", "title": "Expenses by Category", "size": "medium"}, {"type": "trend-line", "title": "Spending Trend", "size": "large"}, {"type": "total-spent", "title": "Total Spent", "size": "small"}, {"type": "reimbursable-amount", "title": "Reimbursable Amount", "size": "small"}], "layout": "grid"}',
                    '{"period": "month"}'
                )
            """)
            conn.commit()
            migrations_applied.append("dashboard_preset")
            print("✓ Dashboard preset table created with defaults")
        
        # Check if homepage_config table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='homepage_config'")
        if not cursor.fetchone():
            print("Applying migration: Creating homepage config table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS homepage_config (
                    id INTEGER NOT NULL PRIMARY KEY,
                    sections TEXT NOT NULL DEFAULT '{}',
                    hero_settings TEXT DEFAULT '{}',
                    table_columns TEXT DEFAULT '{}',
                    widget_layout VARCHAR(20) DEFAULT '2-column',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create default config
            cursor.execute("""
                INSERT INTO homepage_config (sections, hero_settings, table_columns, widget_layout) VALUES (
                    '{"hero": {"visible": true, "order": 1}, "stats": {"visible": true, "order": 2}, "recent_expenses": {"visible": true, "order": 3}, "quick_actions": {"visible": true, "order": 4}, "tips": {"visible": true, "order": 5}}',
                    '{"title": "Pocket Change Showdown", "subtitle": "Track every penny of your PCS move expenses", "show_logo": true}',
                    '{"recent_expenses": ["date", "title", "category", "amount", "reimbursable"]}',
                    '2-column'
                )
            """)
            conn.commit()
            migrations_applied.append("homepage_config")
            print("✓ Homepage config table created with defaults")
        
        # Update database version after migrations
        if migrations_applied:
            update_database_version(cursor, CURRENT_VERSION)
            conn.commit()
            print(f"✅ Applied {len(migrations_applied)} migration(s): {', '.join(migrations_applied)}")
            print(f"✅ Database version updated to {CURRENT_VERSION}")
        else:
            # Even if no migrations, update version if it's different
            if current_db_version != CURRENT_VERSION:
                update_database_version(cursor, CURRENT_VERSION)
                conn.commit()
                print(f"✅ Database version updated to {CURRENT_VERSION}")
            else:
                print("✅ Database schema is up to date")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database check error: {e}")
        return False

def initialize_database(app, db):
    """Initialize database with SQLAlchemy models and default data"""
    from app import Category, PaymentMethod, DashboardPreset, HomepageConfig, Settings
    
    with app.app_context():
        # Create all tables
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Error creating tables: {e}")
            # Tables might already exist
        
        # Check if we need to add default data
        try:
            category_count = Category.query.count()
        except Exception as e:
            print(f"Warning: Error querying categories: {e}")
            category_count = 0
            
        if category_count == 0:
            print("Creating default categories...")
            default_categories = [
                {'name': 'Travel', 'color': '#0d6efd', 'icon': 'fa-plane', 'description': 'Transportation and travel expenses'},
                {'name': 'Lodging', 'color': '#28a745', 'icon': 'fa-bed', 'description': 'Hotels and temporary accommodation'},
                {'name': 'Meals', 'color': '#dc3545', 'icon': 'fa-utensils', 'description': 'Food and dining expenses'},
                {'name': 'Moving', 'color': '#ffc107', 'icon': 'fa-truck-moving', 'description': 'Moving and shipping costs'},
                {'name': 'Storage', 'color': '#17a2b8', 'icon': 'fa-warehouse', 'description': 'Storage facility fees'},
                {'name': 'Car Rental', 'color': '#6f42c1', 'icon': 'fa-car', 'description': 'Vehicle rental expenses'},
                {'name': 'Fuel', 'color': '#fd7e14', 'icon': 'fa-gas-pump', 'description': 'Gas and fuel costs'},
                {'name': 'Utilities', 'color': '#20c997', 'icon': 'fa-plug', 'description': 'Connection and utility fees'},
                {'name': 'Administrative', 'color': '#e83e8c', 'icon': 'fa-file-alt', 'description': 'Paperwork and admin fees'},
                {'name': 'Miscellaneous', 'color': '#6c757d', 'icon': 'fa-tag', 'description': 'Other PCS-related expenses'}
            ]
            
            try:
                for cat_data in default_categories:
                    category = Category(**cat_data)
                    db.session.add(category)
                db.session.commit()
                print("✓ Default categories created")
            except Exception as e:
                db.session.rollback()
                print(f"Warning: Categories might already exist: {e}")
        
        try:
            payment_method_count = PaymentMethod.query.count()
        except Exception:
            payment_method_count = 0
            
        if payment_method_count == 0:
            print("Creating default payment methods...")
            default_methods = [
                {'name': 'Credit Card', 'icon': 'fa-credit-card'},
                {'name': 'Debit Card', 'icon': 'fa-credit-card'},
                {'name': 'Cash', 'icon': 'fa-money-bill'},
                {'name': 'Check', 'icon': 'fa-check'},
                {'name': 'Bank Transfer', 'icon': 'fa-university'},
                {'name': 'PayPal', 'icon': 'fa-paypal'},
                {'name': 'Other', 'icon': 'fa-question-circle'}
            ]
            
            try:
                for method_data in default_methods:
                    method = PaymentMethod(**method_data)
                    db.session.add(method)
                db.session.commit()
                print("✓ Default payment methods created")
            except Exception as e:
                db.session.rollback()
                print(f"Warning: Payment methods might already exist: {e}")
        
        # Ensure default dashboard preset exists
        try:
            if not DashboardPreset.query.filter_by(is_default=True).first():
                if DashboardPreset.query.count() == 0:
                    print("Creating default dashboard preset...")
                    preset = DashboardPreset(
                        name='Default Dashboard',
                        is_default=True,
                        config='{"widgets": [{"type": "category-pie", "title": "Expenses by Category", "size": "medium"}, {"type": "trend-line", "title": "Spending Trend", "size": "large"}, {"type": "total-spent", "title": "Total Spent", "size": "small"}, {"type": "reimbursable-amount", "title": "Reimbursable Amount", "size": "small"}], "layout": "grid"}',
                        filters='{"period": "month"}'
                    )
                    db.session.add(preset)
                    db.session.commit()
                    print("✓ Default dashboard preset created")
        except Exception as e:
            db.session.rollback()
            print(f"Warning: Dashboard preset might already exist: {e}")
        
        # Ensure homepage config exists
        try:
            if HomepageConfig.query.count() == 0:
                print("Creating default homepage configuration...")
                config = HomepageConfig(
                    sections='{"hero": {"visible": true, "order": 1}, "stats": {"visible": true, "order": 2}, "recent_expenses": {"visible": true, "order": 3}, "quick_actions": {"visible": true, "order": 4}, "tips": {"visible": true, "order": 5}}',
                    hero_settings='{"title": "Pocket Change Showdown", "subtitle": "Track every penny of your PCS move expenses", "show_logo": true}',
                    table_columns='{"recent_expenses": ["date", "title", "category", "amount", "reimbursable"]}',
                    widget_layout='2-column'
                )
                db.session.add(config)
                db.session.commit()
                print("✓ Default homepage configuration created")
        except Exception as e:
            db.session.rollback()
            print(f"Warning: Homepage config might already exist: {e}")
        
        # Ensure settings exist with version info
        try:
            settings = Settings.query.first()
            if not settings:
                print("Creating default settings...")
                settings = Settings(db_version=CURRENT_VERSION, app_version=CURRENT_VERSION)
                db.session.add(settings)
                db.session.commit()
                print(f"✓ Default settings created with version {CURRENT_VERSION}")
            else:
                # Update version if different
                if settings.db_version != CURRENT_VERSION:
                    settings.db_version = CURRENT_VERSION
                    settings.app_version = CURRENT_VERSION
                    db.session.commit()
                    print(f"✓ Settings version updated to {CURRENT_VERSION}")
        except Exception as e:
            db.session.rollback()
            print(f"Warning: Settings initialization issue: {e}")
        
        print("✅ Database initialization complete")

def run_auto_migration():
    """Main function to run automatic database migration"""
    print("PCS Tracker - Automatic Database Migration")
    print("==========================================")
    
    # Ensure data directory exists
    data_dir = ensure_database_directory()
    db_path = os.path.join(data_dir, 'pcs_tracker.db')
    
    # Check and apply migrations
    if check_and_migrate_database(db_path):
        print("✅ Database ready for use")
        return True
    else:
        print("❌ Database migration failed")
        return False

if __name__ == '__main__':
    # Can be run standalone for testing
    run_auto_migration()