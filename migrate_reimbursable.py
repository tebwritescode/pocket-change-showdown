#!/usr/bin/env python3
"""
Standalone migration script for reimbursable status enum conversion.
This script can be used to manually run or rollback the migration.
"""

import os
import sys
import argparse
from db_init import check_and_migrate_database, rollback_reimbursable_enum_migration, ensure_database_directory

def main():
    parser = argparse.ArgumentParser(description='PCS Tracker Reimbursable Status Migration')
    parser.add_argument('action', choices=['migrate', 'rollback'], 
                       help='Action to perform: migrate or rollback')
    parser.add_argument('--db-path', type=str, 
                       help='Path to database file (default: data/pcs_tracker.db)')
    
    args = parser.parse_args()
    
    # Determine database path
    if args.db_path:
        db_path = args.db_path
    else:
        data_dir = ensure_database_directory()
        db_path = os.path.join(data_dir, 'pcs_tracker.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        sys.exit(1)
    
    print(f"📁 Using database: {db_path}")
    
    if args.action == 'migrate':
        print("🔄 Running reimbursable status migration...")
        success = check_and_migrate_database(db_path)
        if success:
            print("✅ Migration completed successfully!")
        else:
            print("❌ Migration failed!")
            sys.exit(1)
    
    elif args.action == 'rollback':
        print("🔄 Rolling back reimbursable status migration...")
        confirm = input("⚠️  This will convert all 'maybe' values to 'no'. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Rollback cancelled by user")
            sys.exit(0)
        
        success = rollback_reimbursable_enum_migration(db_path)
        if success:
            print("✅ Rollback completed successfully!")
        else:
            print("❌ Rollback failed!")
            sys.exit(1)

if __name__ == '__main__':
    main()