#!/usr/bin/env python3

"""
Database initialization script for PCS Tracker
Creates the database and populates it with default data.
"""

import os
import sys
from app import app, db, Category, PaymentMethod, DashboardPreset, HomepageConfig

def create_default_categories():
    """Create default expense categories"""
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
    
    for cat_data in default_categories:
        if not Category.query.filter_by(name=cat_data['name']).first():
            category = Category(**cat_data)
            db.session.add(category)
            print(f"Created category: {cat_data['name']}")
    
    db.session.commit()

def create_default_payment_methods():
    """Create default payment methods"""
    default_methods = [
        {'name': 'Credit Card', 'icon': 'fa-credit-card'},
        {'name': 'Debit Card', 'icon': 'fa-credit-card'},
        {'name': 'Cash', 'icon': 'fa-money-bill'},
        {'name': 'Check', 'icon': 'fa-check'},
        {'name': 'Bank Transfer', 'icon': 'fa-university'},
        {'name': 'PayPal', 'icon': 'fa-paypal'},
        {'name': 'Other', 'icon': 'fa-question-circle'}
    ]
    
    for method_data in default_methods:
        if not PaymentMethod.query.filter_by(name=method_data['name']).first():
            method = PaymentMethod(**method_data)
            db.session.add(method)
            print(f"Created payment method: {method_data['name']}")
    
    db.session.commit()

def create_default_dashboard_preset():
    """Create default dashboard preset"""
    if not DashboardPreset.query.first():
        preset = DashboardPreset(
            name='Default Dashboard',
            is_default=True,
            config='{"widgets": [{"type": "category-pie", "title": "Expenses by Category", "size": "medium"}, {"type": "trend-line", "title": "Spending Trend", "size": "large"}, {"type": "total-spent", "title": "Total Spent", "size": "small"}, {"type": "reimbursable-amount", "title": "Reimbursable Amount", "size": "small"}], "layout": "grid"}',
            filters='{"period": "month"}'
        )
        db.session.add(preset)
        print("Created default dashboard preset")
        db.session.commit()

def create_default_homepage_config():
    """Create default homepage configuration"""
    if not HomepageConfig.query.first():
        config = HomepageConfig(
            sections='{"hero": {"visible": true, "order": 1}, "stats": {"visible": true, "order": 2}, "recent_expenses": {"visible": true, "order": 3}, "quick_actions": {"visible": true, "order": 4}, "tips": {"visible": true, "order": 5}}',
            hero_settings='{"title": "Pocket Change Showdown", "subtitle": "Track every penny of your PCS move expenses", "show_logo": true}',
            table_columns='{"recent_expenses": ["date", "title", "category", "amount", "reimbursable"]}',
            widget_layout='2-column'
        )
        db.session.add(config)
        print("Created default homepage configuration")
        db.session.commit()

def main():
    """Initialize the database"""
    print("PCS Tracker Database Initialization")
    print("==================================")
    
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        print(f"Creating data directory: {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
    
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created")
            
            print("Creating default categories...")
            create_default_categories()
            print("✓ Default categories created")
            
            print("Creating default payment methods...")
            create_default_payment_methods()
            print("✓ Default payment methods created")
            
            print("Creating default dashboard preset...")
            create_default_dashboard_preset()
            print("✓ Default dashboard preset created")
            
            print("Creating default homepage configuration...")
            create_default_homepage_config()
            print("✓ Default homepage configuration created")
            
            print("\n✅ Database initialization completed successfully!")
            print("You can now start using PCS Tracker.")
            
        except Exception as e:
            print(f"\n❌ Database initialization failed: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()