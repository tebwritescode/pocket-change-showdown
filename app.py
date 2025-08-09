from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, FileField, DateField, HiddenField, FieldList, FormField
from wtforms.validators import Optional, ValidationError
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import pandas as pd
import io
import base64
import json
from collections import defaultdict
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pcs-showdown-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/pcs_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database Models
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    color_scheme = db.Column(db.String(50), default='default')
    default_view = db.Column(db.String(20), default='list')
    categories = db.Column(db.Text, default='[]')
    payment_methods = db.Column(db.Text, default='[]')
    custom_fields = db.Column(db.Text, default='{}')
    
    def get_categories(self):
        try:
            return json.loads(self.categories) if self.categories else []
        except:
            return []
    
    def get_payment_methods(self):
        try:
            return json.loads(self.payment_methods) if self.payment_methods else []
        except:
            return []
            
    def get_custom_fields(self):
        try:
            return json.loads(self.custom_fields) if self.custom_fields else {}
        except:
            return {}

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(200))
    color = db.Column(db.String(7), default='#0d6efd')
    icon = db.Column(db.String(50), default='fa-tag')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PaymentMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    icon = db.Column(db.String(50), default='fa-credit-card')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    cost = db.Column(db.Float, default=0.0)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'))
    date = db.Column(db.Date, default=datetime.utcnow)
    receipt_image = db.Column(db.LargeBinary)
    receipt_filename = db.Column(db.String(200))
    receipt_mimetype = db.Column(db.String(100))
    location = db.Column(db.String(200))
    vendor = db.Column(db.String(200))
    notes = db.Column(db.Text)
    tags = db.Column(db.String(500))
    custom_data = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = db.relationship('Category', backref='expenses')
    payment_method = db.relationship('PaymentMethod', backref='expenses')
    
    def get_custom_data(self):
        try:
            return json.loads(self.custom_data) if self.custom_data else {}
        except:
            return {}
    
    def set_custom_data(self, data):
        self.custom_data = json.dumps(data)

# Forms
class ExpenseForm(FlaskForm):
    title = StringField('Title', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    cost = FloatField('Cost ($)', validators=[Optional()])
    payment_method_id = SelectField('Payment Method', coerce=int, validators=[Optional()])
    date = DateField('Date', validators=[Optional()], default=datetime.today)
    receipt = FileField('Receipt/Screenshot', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    vendor = StringField('Vendor', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    tags = StringField('Tags (comma-separated)', validators=[Optional()])

class CategoryForm(FlaskForm):
    name = StringField('Category Name')
    description = StringField('Description', validators=[Optional()])
    color = StringField('Color', default='#0d6efd', validators=[Optional()])
    icon = StringField('Icon Class', default='fa-tag', validators=[Optional()])

class PaymentMethodForm(FlaskForm):
    name = StringField('Payment Method')
    icon = StringField('Icon Class', default='fa-credit-card', validators=[Optional()])

class SettingsForm(FlaskForm):
    color_scheme = SelectField('Color Scheme', choices=[
        ('default', 'Default Blue'),
        ('dark', 'Dark Theme'),
        ('green', 'Nature Green'),
        ('purple', 'Royal Purple'),
        ('orange', 'Vibrant Orange'),
        ('teal', 'Ocean Teal'),
        ('red', 'Bold Red'),
        ('pink', 'Soft Pink')
    ])
    default_view = SelectField('Default View', choices=[
        ('list', 'List View'),
        ('grid', 'Grid View'),
        ('dashboard', 'Dashboard')
    ])

# Initialize default data
def init_defaults():
    # Default categories
    default_categories = [
        {'name': 'Moving', 'icon': 'fa-truck', 'color': '#0d6efd'},
        {'name': 'Travel', 'icon': 'fa-plane', 'color': '#28a745'},
        {'name': 'Housing', 'icon': 'fa-home', 'color': '#dc3545'},
        {'name': 'Storage', 'icon': 'fa-warehouse', 'color': '#ffc107'},
        {'name': 'Transportation', 'icon': 'fa-car', 'color': '#17a2b8'},
        {'name': 'Lodging', 'icon': 'fa-bed', 'color': '#6f42c1'},
        {'name': 'Food', 'icon': 'fa-utensils', 'color': '#fd7e14'},
        {'name': 'Supplies', 'icon': 'fa-box', 'color': '#20c997'},
        {'name': 'Services', 'icon': 'fa-concierge-bell', 'color': '#e83e8c'},
        {'name': 'Other', 'icon': 'fa-ellipsis-h', 'color': '#6c757d'}
    ]
    
    # Default payment methods
    default_payment_methods = [
        {'name': 'Cash', 'icon': 'fa-money-bill'},
        {'name': 'Credit Card', 'icon': 'fa-credit-card'},
        {'name': 'Debit Card', 'icon': 'fa-credit-card'},
        {'name': 'Check', 'icon': 'fa-money-check'},
        {'name': 'Bank Transfer', 'icon': 'fa-university'},
        {'name': 'PayPal', 'icon': 'fab fa-paypal'},
        {'name': 'Venmo', 'icon': 'fa-mobile-alt'},
        {'name': 'Company Card', 'icon': 'fa-building'},
        {'name': 'Reimbursement', 'icon': 'fa-hand-holding-usd'},
        {'name': 'Other', 'icon': 'fa-question-circle'}
    ]
    
    # Check if categories exist
    if Category.query.count() == 0:
        for cat in default_categories:
            category = Category(
                name=cat['name'],
                icon=cat['icon'],
                color=cat['color'],
                is_default=True
            )
            db.session.add(category)
    
    # Check if payment methods exist
    if PaymentMethod.query.count() == 0:
        for pm in default_payment_methods:
            payment_method = PaymentMethod(
                name=pm['name'],
                icon=pm['icon'],
                is_default=True
            )
            db.session.add(payment_method)
    
    # Check if settings exist
    if Settings.query.count() == 0:
        settings = Settings(color_scheme='default')
        db.session.add(settings)
    
    db.session.commit()

# Template context functions
@app.context_processor
def inject_helper_functions():
    def get_recent_expenses(limit=5):
        return Expense.query.order_by(Expense.date.desc(), Expense.created_at.desc()).limit(limit).all()
    
    def get_monthly_total():
        today = datetime.today()
        start_of_month = today.replace(day=1)
        expenses = Expense.query.filter(Expense.date >= start_of_month).all()
        return sum(e.cost or 0 for e in expenses)
    
    def get_expense_count():
        return Expense.query.count()
    
    return dict(
        get_recent_expenses=get_recent_expenses,
        get_monthly_total=get_monthly_total,
        get_expense_count=get_expense_count
    )

# Routes
@app.route('/')
def index():
    settings = Settings.query.first()
    
    # Get statistics for the homepage
    today = datetime.today()
    month_start = today.replace(day=1)
    
    all_expenses = Expense.query.all()
    month_expenses_query = Expense.query.filter(Expense.date >= month_start).all()
    recent_expenses = Expense.query.order_by(Expense.date.desc(), Expense.created_at.desc()).limit(5).all()
    
    total_expenses = sum(e.cost or 0 for e in all_expenses)
    month_expenses = sum(e.cost or 0 for e in month_expenses_query)
    expense_count = len(all_expenses)
    category_count = Category.query.count()
    
    return render_template('index.html', 
                         settings=settings,
                         total_expenses=total_expenses,
                         month_expenses=month_expenses,
                         expense_count=expense_count,
                         category_count=category_count,
                         recent_expenses=recent_expenses)

@app.route('/expenses')
def expenses():
    settings = Settings.query.first()
    expenses_list = Expense.query.order_by(Expense.date.desc(), Expense.created_at.desc()).all()
    total_cost = sum(e.cost or 0 for e in expenses_list)
    categories = Category.query.all()
    payment_methods = PaymentMethod.query.all()
    return render_template('expenses.html', 
                         expenses=expenses_list, 
                         total_cost=total_cost, 
                         settings=settings,
                         categories=categories,
                         payment_methods=payment_methods)

@app.route('/expense/new', methods=['GET', 'POST'])
def new_expense():
    settings = Settings.query.first()
    form = ExpenseForm()
    
    # Populate category choices
    categories = Category.query.order_by(Category.name).all()
    form.category_id.choices = [(0, 'Select Category')] + [(c.id, c.name) for c in categories]
    
    # Populate payment method choices
    payment_methods = PaymentMethod.query.order_by(PaymentMethod.name).all()
    form.payment_method_id.choices = [(0, 'Select Payment Method')] + [(p.id, p.name) for p in payment_methods]
    
    if form.validate_on_submit():
        expense = Expense()
        expense.title = form.title.data or 'Untitled Expense'
        expense.description = form.description.data
        expense.category_id = form.category_id.data if form.category_id.data != 0 else None
        expense.cost = form.cost.data or 0
        expense.payment_method_id = form.payment_method_id.data if form.payment_method_id.data != 0 else None
        expense.date = form.date.data
        expense.location = form.location.data
        expense.vendor = form.vendor.data
        expense.notes = form.notes.data
        expense.tags = form.tags.data
        
        # Handle file upload
        if form.receipt.data:
            file = form.receipt.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_data = file.read()
                expense.receipt_image = file_data
                expense.receipt_filename = filename
                expense.receipt_mimetype = file.content_type
        
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('expense_form.html', form=form, settings=settings, is_edit=False)

@app.route('/expense/<int:id>/edit', methods=['GET', 'POST'])
def edit_expense(id):
    settings = Settings.query.first()
    expense = Expense.query.get_or_404(id)
    form = ExpenseForm(obj=expense)
    
    # Populate category choices
    categories = Category.query.order_by(Category.name).all()
    form.category_id.choices = [(0, 'Select Category')] + [(c.id, c.name) for c in categories]
    
    # Populate payment method choices
    payment_methods = PaymentMethod.query.order_by(PaymentMethod.name).all()
    form.payment_method_id.choices = [(0, 'Select Payment Method')] + [(p.id, p.name) for p in payment_methods]
    
    if form.validate_on_submit():
        expense.title = form.title.data or 'Untitled Expense'
        expense.description = form.description.data
        expense.category_id = form.category_id.data if form.category_id.data != 0 else None
        expense.cost = form.cost.data or 0
        expense.payment_method_id = form.payment_method_id.data if form.payment_method_id.data != 0 else None
        expense.date = form.date.data
        expense.location = form.location.data
        expense.vendor = form.vendor.data
        expense.notes = form.notes.data
        expense.tags = form.tags.data
        expense.updated_at = datetime.utcnow()
        
        # Handle file upload
        if form.receipt.data:
            file = form.receipt.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_data = file.read()
                expense.receipt_image = file_data
                expense.receipt_filename = filename
                expense.receipt_mimetype = file.content_type
        
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('expense_form.html', form=form, expense=expense, settings=settings, is_edit=True)

@app.route('/expense/<int:id>/delete', methods=['POST'])
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses'))

@app.route('/expense/<int:id>/receipt')
def view_receipt(id):
    expense = Expense.query.get_or_404(id)
    if expense.receipt_image:
        return send_file(
            io.BytesIO(expense.receipt_image),
            mimetype=expense.receipt_mimetype or 'image/jpeg',
            as_attachment=False,
            download_name=expense.receipt_filename or 'receipt.jpg'
        )
    flash('No receipt found for this expense', 'warning')
    return redirect(url_for('expenses'))

@app.route('/dashboard')
def dashboard():
    settings = Settings.query.first()
    
    # Get date range for filtering
    period = request.args.get('period', 'month')
    today = datetime.today()
    
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'quarter':
        start_date = today - timedelta(days=90)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)
    
    expenses_query = Expense.query.filter(Expense.date >= start_date)
    all_expenses = expenses_query.all()
    
    # Calculate statistics
    total_expenses = sum(e.cost or 0 for e in all_expenses)
    expense_count = len(all_expenses)
    avg_expense = total_expenses / expense_count if expense_count > 0 else 0
    
    # Get top categories
    category_totals = defaultdict(float)
    for expense in all_expenses:
        if expense.category:
            category_totals[expense.category.name] += expense.cost or 0
    
    # Get payment method breakdown
    payment_totals = defaultdict(float)
    for expense in all_expenses:
        if expense.payment_method:
            payment_totals[expense.payment_method.name] += expense.cost or 0
    
    return render_template('dashboard.html', 
                         settings=settings,
                         total_expenses=total_expenses,
                         expense_count=expense_count,
                         avg_expense=avg_expense,
                         period=period)

@app.route('/api/expense_data')
def api_expense_data():
    period = request.args.get('period', 'month')
    today = datetime.today()
    
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'quarter':
        start_date = today - timedelta(days=90)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)
    
    expenses = Expense.query.filter(Expense.date >= start_date).all()
    
    # Category breakdown
    category_data = defaultdict(float)
    for expense in expenses:
        category_name = expense.category.name if expense.category else 'Uncategorized'
        category_data[category_name] += expense.cost or 0
    
    # Payment method breakdown
    payment_data = defaultdict(float)
    for expense in expenses:
        payment_name = expense.payment_method.name if expense.payment_method else 'Unknown'
        payment_data[payment_name] += expense.cost or 0
    
    # Daily trend
    daily_data = defaultdict(float)
    for expense in expenses:
        date_str = expense.date.strftime('%Y-%m-%d') if expense.date else 'Unknown'
        daily_data[date_str] += expense.cost or 0
    
    return jsonify({
        'categories': {
            'labels': list(category_data.keys()),
            'data': list(category_data.values())
        },
        'payment_methods': {
            'labels': list(payment_data.keys()),
            'data': list(payment_data.values())
        },
        'daily_trend': {
            'labels': sorted(daily_data.keys()),
            'data': [daily_data[k] for k in sorted(daily_data.keys())]
        }
    })

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    
    form = SettingsForm(obj=settings)
    
    if form.validate_on_submit():
        settings.color_scheme = form.color_scheme.data
        settings.default_view = form.default_view.data
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings_page'))
    
    categories = Category.query.order_by(Category.name).all()
    payment_methods = PaymentMethod.query.order_by(PaymentMethod.name).all()
    expenses = Expense.query.all()
    
    return render_template('settings.html', 
                         form=form, 
                         settings=settings,
                         categories=categories,
                         payment_methods=payment_methods,
                         expenses=expenses)

@app.route('/settings/category/add', methods=['POST'])
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            color=form.color.data,
            icon=form.icon.data
        )
        db.session.add(category)
        db.session.commit()
        flash(f'Category "{form.name.data}" added successfully!', 'success')
    return redirect(url_for('settings_page'))

@app.route('/settings/category/<int:id>/delete', methods=['POST'])
def delete_category(id):
    category = Category.query.get_or_404(id)
    if not category.is_default:
        # Update expenses to remove this category
        Expense.query.filter_by(category_id=id).update({'category_id': None})
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category.name}" deleted successfully!', 'success')
    else:
        flash('Cannot delete default categories', 'warning')
    return redirect(url_for('settings_page'))

@app.route('/settings/payment/add', methods=['POST'])
def add_payment_method():
    form = PaymentMethodForm()
    if form.validate_on_submit():
        payment = PaymentMethod(
            name=form.name.data,
            icon=form.icon.data
        )
        db.session.add(payment)
        db.session.commit()
        flash(f'Payment method "{form.name.data}" added successfully!', 'success')
    return redirect(url_for('settings_page'))

@app.route('/settings/payment/<int:id>/delete', methods=['POST'])
def delete_payment_method(id):
    payment = PaymentMethod.query.get_or_404(id)
    if not payment.is_default:
        # Update expenses to remove this payment method
        Expense.query.filter_by(payment_method_id=id).update({'payment_method_id': None})
        db.session.delete(payment)
        db.session.commit()
        flash(f'Payment method "{payment.name}" deleted successfully!', 'success')
    else:
        flash('Cannot delete default payment methods', 'warning')
    return redirect(url_for('settings_page'))

@app.route('/export')
def export_csv():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Title', 'Description', 'Category', 'Cost', 'Payment Method', 
                    'Location', 'Vendor', 'Notes', 'Tags', 'Has Receipt'])
    
    # Write data
    for expense in expenses:
        writer.writerow([
            expense.date.strftime('%Y-%m-%d') if expense.date else '',
            expense.title or '',
            expense.description or '',
            expense.category.name if expense.category else '',
            expense.cost or 0,
            expense.payment_method.name if expense.payment_method else '',
            expense.location or '',
            expense.vendor or '',
            expense.notes or '',
            expense.tags or '',
            'Yes' if expense.receipt_image else 'No'
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'pcs_expenses_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/import', methods=['GET', 'POST'])
def import_csv():
    settings = Settings.query.first()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'warning')
            return redirect(url_for('import_csv'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'warning')
            return redirect(url_for('import_csv'))
        
        if file and file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
                
                # Get category and payment method mappings
                categories = {c.name: c.id for c in Category.query.all()}
                payment_methods = {p.name: p.id for p in PaymentMethod.query.all()}
                
                imported_count = 0
                for _, row in df.iterrows():
                    expense = Expense()
                    expense.title = row.get('Title', 'Imported Expense')
                    expense.description = row.get('Description', '')
                    expense.cost = float(row.get('Cost', 0))
                    expense.location = row.get('Location', '')
                    expense.vendor = row.get('Vendor', '')
                    expense.notes = row.get('Notes', '')
                    expense.tags = row.get('Tags', '')
                    
                    # Parse date
                    if 'Date' in row and pd.notna(row['Date']):
                        try:
                            expense.date = pd.to_datetime(row['Date']).date()
                        except:
                            expense.date = datetime.today().date()
                    
                    # Map category
                    if 'Category' in row and row['Category'] in categories:
                        expense.category_id = categories[row['Category']]
                    
                    # Map payment method
                    if 'Payment Method' in row and row['Payment Method'] in payment_methods:
                        expense.payment_method_id = payment_methods[row['Payment Method']]
                    
                    db.session.add(expense)
                    imported_count += 1
                
                db.session.commit()
                flash(f'Successfully imported {imported_count} expenses!', 'success')
                return redirect(url_for('expenses'))
                
            except Exception as e:
                flash(f'Error importing file: {str(e)}', 'danger')
                return redirect(url_for('import_csv'))
    
    categories = Category.query.all()
    payment_methods = PaymentMethod.query.all()
    return render_template('import.html', settings=settings, categories=categories, payment_methods=payment_methods)

@app.route('/template')
def download_template():
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Title', 'Description', 'Category', 'Cost', 'Payment Method', 
                    'Location', 'Vendor', 'Notes', 'Tags'])
    
    # Add sample rows
    writer.writerow(['2024-01-15', 'Moving Truck Rental', 'U-Haul 26ft truck', 'Moving', '299.99', 
                    'Credit Card', 'U-Haul Downtown', 'U-Haul', 'Included insurance', 'moving,transport'])
    writer.writerow(['2024-01-16', 'Hotel Stay', 'Overnight during move', 'Lodging', '125.00', 
                    'Company Card', 'Holiday Inn Express', 'Holiday Inn', '1 night stay', 'lodging,travel'])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='pcs_import_template.csv'
    )

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 16MB.', 'danger')
    return redirect(url_for('new_expense'))

# Create tables and initialize data
with app.app_context():
    os.makedirs('data', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    db.create_all()
    init_defaults()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)