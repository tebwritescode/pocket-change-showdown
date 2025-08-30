from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms.csrf.core import CSRF
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
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, legal
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics import renderPDF
from PIL import Image as PILImage
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from io import BytesIO
from pdf_utils import create_pie_chart, create_bar_chart, create_trend_chart, calculate_monthly_breakdown

# Simple in-memory cache
CACHE = {}
CACHE_TIMEOUT = 300  # 5 minutes

def get_cache_key(endpoint, **kwargs):
    """Generate a cache key from endpoint and parameters"""
    params_str = '&'.join([f"{k}={v}" for k, v in sorted(kwargs.items())])
    return f"{endpoint}:{params_str}"

def get_from_cache(key):
    """Get value from cache if not expired"""
    if key in CACHE:
        timestamp, value = CACHE[key]
        if time.time() - timestamp < CACHE_TIMEOUT:
            return value
        else:
            del CACHE[key]
    return None

def set_cache(key, value):
    """Set value in cache with current timestamp"""
    CACHE[key] = (time.time(), value)

def clear_cache():
    """Clear all cached data"""
    CACHE.clear()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pcs-showdown-secret-key-2024')
# Use absolute path for database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "data", "pcs_tracker.db")}'
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
    db_version = db.Column(db.String(20), default='2.0.0')  # Track database schema version
    app_version = db.Column(db.String(20), default='2.1.0')  # Track app version that last updated DB
    
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

class DashboardPreset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    config = db.Column(db.Text, nullable=False)  # JSON string with widget configuration
    filters = db.Column(db.Text, default='{}')  # JSON string with filter settings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_config(self):
        try:
            return json.loads(self.config) if self.config else {}
        except:
            return {}
    
    def set_config(self, data):
        self.config = json.dumps(data)
    
    def get_filters(self):
        try:
            return json.loads(self.filters) if self.filters else {}
        except:
            return {}
    
    def set_filters(self, data):
        self.filters = json.dumps(data)

class HomepageConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sections = db.Column(db.Text, nullable=False, default='{}')  # JSON with section visibility/order
    hero_settings = db.Column(db.Text, default='{}')  # JSON with hero customization
    table_columns = db.Column(db.Text, default='{}')  # JSON with table column settings
    widget_layout = db.Column(db.String(20), default='2-column')  # 1-column, 2-column, 3-column
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_sections(self):
        try:
            return json.loads(self.sections) if self.sections else {}
        except:
            return {}
    
    def set_sections(self, data):
        self.sections = json.dumps(data)
    
    def get_hero_settings(self):
        try:
            return json.loads(self.hero_settings) if self.hero_settings else {}
        except:
            return {}
    
    def set_hero_settings(self, data):
        self.hero_settings = json.dumps(data)
    
    def get_table_columns(self):
        try:
            return json.loads(self.table_columns) if self.table_columns else {}
        except:
            return {}
    
    def set_table_columns(self, data):
        self.table_columns = json.dumps(data)

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
    is_reimbursable = db.Column(db.Boolean, default=False)
    reimbursement_status = db.Column(db.String(20), default='none')  # none, pending, approved, received
    reimbursement_notes = db.Column(db.Text)
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
class BaseForm(FlaskForm):
    class Meta:
        csrf = False

class ExpenseForm(BaseForm):
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
    is_reimbursable = SelectField('Reimbursable', choices=[(0, 'No'), (1, 'Yes')], coerce=int, validators=[Optional()])
    reimbursement_status = SelectField('Reimbursement Status', choices=[
        ('none', 'Not Applicable'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('received', 'Received')
    ], validators=[Optional()])
    reimbursement_notes = TextAreaField('Reimbursement Notes', validators=[Optional()])

class CategoryForm(BaseForm):
    name = StringField('Category Name')
    description = StringField('Description', validators=[Optional()])
    color = StringField('Color', default='#0d6efd', validators=[Optional()])
    icon = StringField('Icon Class', default='fa-tag', validators=[Optional()])

class PaymentMethodForm(BaseForm):
    name = StringField('Payment Method')
    icon = StringField('Icon Class', default='fa-credit-card', validators=[Optional()])

class SettingsForm(BaseForm):
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

# Custom template filters
@app.template_filter('currency')
def currency_filter(value):
    """Format a number as currency with commas and 2 decimal places"""
    try:
        value = float(value or 0)
        return "{:,.2f}".format(value)
    except (ValueError, TypeError):
        return "0.00"

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

# Static file serving
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

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
        expense.is_reimbursable = bool(form.is_reimbursable.data)
        expense.reimbursement_status = form.reimbursement_status.data if form.is_reimbursable.data else 'none'
        expense.reimbursement_notes = form.reimbursement_notes.data if form.is_reimbursable.data else None
        
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
        clear_cache()  # Invalidate cache after adding expense
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
        expense.is_reimbursable = bool(form.is_reimbursable.data)
        expense.reimbursement_status = form.reimbursement_status.data if form.is_reimbursable.data else 'none'
        expense.reimbursement_notes = form.reimbursement_notes.data if form.is_reimbursable.data else None
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
        clear_cache()  # Invalidate cache after updating expense
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('expense_form.html', form=form, expense=expense, settings=settings, is_edit=True)

@app.route('/expense/<int:id>/delete', methods=['POST'])
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    clear_cache()  # Invalidate cache after deleting expense
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

@app.route('/dashboard/customize')
def dashboard_customize():
    settings = Settings.query.first()
    categories = Category.query.all()
    payment_methods = PaymentMethod.query.all()
    presets = DashboardPreset.query.all()
    
    # Get current preset or default config
    default_preset = DashboardPreset.query.filter_by(is_default=True).first()
    
    return render_template('dashboard_config.html',
                         settings=settings,
                         categories=categories,
                         payment_methods=payment_methods,
                         presets=presets,
                         default_preset=default_preset)

@app.route('/api/expense_data')
def api_expense_data():
    period = request.args.get('period', 'month')
    categories_filter = request.args.getlist('categories[]')
    payment_methods_filter = request.args.getlist('payment_methods[]')
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)
    reimbursable_only = request.args.get('reimbursable_only', 'false').lower() == 'true'
    reimbursement_status = request.args.get('reimbursement_status')
    
    # Check cache first
    cache_key = get_cache_key('expense_data',
        period=period,
        categories=','.join(map(str, categories_filter)) if categories_filter else '',
        payment_methods=','.join(map(str, payment_methods_filter)) if payment_methods_filter else '',
        min_amount=min_amount or '',
        max_amount=max_amount or '',
        reimbursable_only=reimbursable_only,
        reimbursement_status=reimbursement_status or ''
    )
    
    cached_result = get_from_cache(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
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
    
    # Build query with filters
    query = Expense.query.filter(Expense.date >= start_date)
    
    if categories_filter:
        query = query.filter(Expense.category_id.in_(categories_filter))
    
    if payment_methods_filter:
        query = query.filter(Expense.payment_method_id.in_(payment_methods_filter))
    
    if min_amount is not None:
        query = query.filter(Expense.cost >= min_amount)
    
    if max_amount is not None:
        query = query.filter(Expense.cost <= max_amount)
    
    if reimbursable_only:
        query = query.filter(Expense.is_reimbursable == True)
    
    if reimbursement_status and reimbursement_status != 'all':
        query = query.filter(Expense.reimbursement_status == reimbursement_status)
    
    expenses = query.all()
    
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
    
    # Reimbursement statistics
    reimbursable_total = sum(e.cost or 0 for e in expenses if e.is_reimbursable)
    pending_reimbursements = sum(e.cost or 0 for e in expenses if e.is_reimbursable and e.reimbursement_status == 'pending')
    approved_reimbursements = sum(e.cost or 0 for e in expenses if e.is_reimbursable and e.reimbursement_status == 'approved')
    received_reimbursements = sum(e.cost or 0 for e in expenses if e.is_reimbursable and e.reimbursement_status == 'received')
    
    result = {
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
        },
        'reimbursement_stats': {
            'total_reimbursable': reimbursable_total,
            'pending': pending_reimbursements,
            'approved': approved_reimbursements,
            'received': received_reimbursements
        },
        'total_expenses': sum(e.cost or 0 for e in expenses),
        'expense_count': len(expenses)
    }
    
    # Cache the result
    set_cache(cache_key, result)
    return jsonify(result)

@app.route('/api/dashboard/presets', methods=['GET', 'POST'])
def api_dashboard_presets():
    if request.method == 'GET':
        presets = DashboardPreset.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'is_default': p.is_default,
            'config': p.get_config(),
            'filters': p.get_filters()
        } for p in presets])
    
    elif request.method == 'POST':
        data = request.json
        preset = DashboardPreset(
            name=data.get('name', 'Untitled Preset'),
            is_default=data.get('is_default', False)
        )
        preset.set_config(data.get('config', {}))
        preset.set_filters(data.get('filters', {}))
        
        # If this is set as default, unset other defaults
        if preset.is_default:
            DashboardPreset.query.update({'is_default': False})
        
        db.session.add(preset)
        db.session.commit()
        
        return jsonify({
            'id': preset.id,
            'name': preset.name,
            'is_default': preset.is_default,
            'config': preset.get_config(),
            'filters': preset.get_filters()
        }), 201

@app.route('/api/dashboard/presets/<int:preset_id>', methods=['GET', 'PUT', 'DELETE'])
def api_dashboard_preset(preset_id):
    preset = DashboardPreset.query.get_or_404(preset_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': preset.id,
            'name': preset.name,
            'is_default': preset.is_default,
            'config': preset.get_config(),
            'filters': preset.get_filters()
        })
    
    elif request.method == 'PUT':
        data = request.json
        preset.name = data.get('name', preset.name)
        
        if 'config' in data:
            preset.set_config(data['config'])
        
        if 'filters' in data:
            preset.set_filters(data['filters'])
        
        # Handle default setting
        if data.get('is_default', False) and not preset.is_default:
            DashboardPreset.query.update({'is_default': False})
            preset.is_default = True
        elif not data.get('is_default', False):
            preset.is_default = False
        
        db.session.commit()
        
        return jsonify({
            'id': preset.id,
            'name': preset.name,
            'is_default': preset.is_default,
            'config': preset.get_config(),
            'filters': preset.get_filters()
        })
    
    elif request.method == 'DELETE':
        db.session.delete(preset)
        db.session.commit()
        return '', 204

@app.route('/api/widgets/data', methods=['GET'])
def api_widgets_data():
    widget_type = request.args.get('type')
    period = request.args.get('period', 'month')
    categories_filter = request.args.getlist('categories[]')
    payment_methods_filter = request.args.getlist('payment_methods[]')
    reimbursable_only = request.args.get('reimbursable_only', 'false').lower() == 'true'
    
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
    
    # Build query with filters
    query = Expense.query.filter(Expense.date >= start_date)
    
    if categories_filter:
        query = query.filter(Expense.category_id.in_(categories_filter))
    
    if payment_methods_filter:
        query = query.filter(Expense.payment_method_id.in_(payment_methods_filter))
    
    if reimbursable_only:
        query = query.filter(Expense.is_reimbursable == True)
    
    expenses = query.all()
    
    # Return data based on widget type
    if widget_type == 'total_spent':
        return jsonify({'value': sum(e.cost or 0 for e in expenses)})
    
    elif widget_type == 'reimbursable_amount':
        return jsonify({'value': sum(e.cost or 0 for e in expenses if e.is_reimbursable)})
    
    elif widget_type == 'pending_reimbursements':
        pending = [e for e in expenses if e.is_reimbursable and e.reimbursement_status == 'pending']
        return jsonify({
            'count': len(pending),
            'total': sum(e.cost or 0 for e in pending)
        })
    
    elif widget_type == 'category_breakdown':
        category_data = defaultdict(float)
        for expense in expenses:
            category_name = expense.category.name if expense.category else 'Uncategorized'
            category_data[category_name] += expense.cost or 0
        return jsonify({
            'labels': list(category_data.keys()),
            'data': list(category_data.values())
        })
    
    elif widget_type == 'recent_expenses':
        recent = sorted(expenses, key=lambda x: x.created_at, reverse=True)[:10]
        return jsonify([{
            'id': e.id,
            'title': e.title or 'Untitled',
            'amount': e.cost or 0,
            'category': e.category.name if e.category else 'Uncategorized',
            'date': e.date.isoformat() if e.date else None,
            'is_reimbursable': e.is_reimbursable,
            'reimbursement_status': e.reimbursement_status
        } for e in recent])
    
    else:
        return jsonify({'error': 'Unknown widget type'}), 400

@app.route('/api/homepage/config', methods=['GET', 'PUT'])
def api_homepage_config():
    config = HomepageConfig.query.first()
    if not config:
        config = HomepageConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'GET':
        return jsonify({
            'sections': config.get_sections(),
            'hero_settings': config.get_hero_settings(),
            'table_columns': config.get_table_columns(),
            'widget_layout': config.widget_layout
        })
    
    elif request.method == 'PUT':
        data = request.json
        
        if 'sections' in data:
            config.set_sections(data['sections'])
        
        if 'hero_settings' in data:
            config.set_hero_settings(data['hero_settings'])
        
        if 'table_columns' in data:
            config.set_table_columns(data['table_columns'])
        
        if 'widget_layout' in data:
            config.widget_layout = data['widget_layout']
        
        db.session.commit()
        
        return jsonify({
            'sections': config.get_sections(),
            'hero_settings': config.get_hero_settings(),
            'table_columns': config.get_table_columns(),
            'widget_layout': config.widget_layout
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

@app.route('/report/config')
def report_config():
    """Show report configuration page"""
    categories = Category.query.order_by(Category.name).all()
    payment_methods = PaymentMethod.query.order_by(PaymentMethod.name).all()
    
    # Default date range (last 30 days)
    default_end_date = datetime.today().date()
    default_start_date = (datetime.today() - timedelta(days=30)).date()
    
    return render_template('report_config.html',
                          categories=categories,
                          payment_methods=payment_methods,
                          default_start_date=default_start_date,
                          default_end_date=default_end_date)

@app.route('/report/pdf')
def generate_pdf_report():
    """Generate a PDF report of expenses with PCS branding"""
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category_id')
    payment_method_id = request.args.get('payment_method_id')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    
    # Get content options
    include_summary = request.args.get('include_summary') == 'on'
    include_category_breakdown = request.args.get('include_category_breakdown') == 'on'
    include_payment_breakdown = request.args.get('include_payment_breakdown') == 'on'
    include_monthly_trend = request.args.get('include_monthly_trend') == 'on'
    include_pie_chart = request.args.get('include_pie_chart') == 'on'
    include_bar_chart = request.args.get('include_bar_chart') == 'on'
    include_trend_chart = request.args.get('include_trend_chart') == 'on'
    include_expense_table = request.args.get('include_expense_table') == 'on'
    include_descriptions = request.args.get('include_descriptions') == 'on'
    include_notes = request.args.get('include_notes') == 'on'
    include_locations = request.args.get('include_locations') == 'on'
    
    # Get report options
    report_title = request.args.get('report_title', 'PCS Expense Report')
    page_size_str = request.args.get('page_size', 'letter')
    include_logo = request.args.get('include_logo') == 'on'
    include_page_numbers = request.args.get('include_page_numbers') == 'on'
    
    # Build query
    query = Expense.query
    
    if start_date:
        query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if category_id and category_id != 'all':
        query = query.filter(Expense.category_id == int(category_id))
    if payment_method_id and payment_method_id != 'all':
        query = query.filter(Expense.payment_method_id == int(payment_method_id))
    if min_amount:
        query = query.filter(Expense.cost >= float(min_amount))
    if max_amount:
        query = query.filter(Expense.cost <= float(max_amount))
    
    expenses = query.order_by(Expense.date.desc()).all()
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Determine page size
    if page_size_str == 'a4':
        page_size = A4
    elif page_size_str == 'legal':
        page_size = legal
    else:
        page_size = letter
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles with PCS branding colors
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=12
    )
    
    normal_style = styles['Normal']
    
    # Add logo if requested
    if include_logo:
        logo_path = os.path.join(os.path.dirname(__file__), 'static', 'img', 'logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=0.67*inch)  # Maintain aspect ratio
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.5*inch))
    
    # Add title
    elements.append(Paragraph(report_title, title_style))
    elements.append(Paragraph("Expense Report", heading_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add report metadata
    metadata_style = ParagraphStyle(
        'Metadata',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6c757d')
    )
    
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", metadata_style))
    elements.append(Paragraph(f"Total Expenses: {len(expenses)}", metadata_style))
    elements.append(Paragraph(f"Total Amount: ${sum(e.cost or 0 for e in expenses):,.2f}", metadata_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Create summary statistics table if requested
    if include_summary:
        summary_data = [
            ['Summary Statistics', ''],
            ['Total Expenses:', f"${sum(e.cost or 0 for e in expenses):,.2f}"],
            ['Number of Transactions:', str(len(expenses))],
            ['Average Expense:', f"${(sum(e.cost or 0 for e in expenses) / len(expenses) if expenses else 0):,.2f}"],
            ['Highest Expense:', f"${max((e.cost or 0 for e in expenses), default=0):,.2f}"],
            ['Lowest Expense:', f"${min((e.cost or 0 for e in expenses), default=0):,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*inch))
    
    # Calculate totals for various breakdowns
    category_totals = defaultdict(float)
    payment_totals = defaultdict(float)
    
    for expense in expenses:
        category_name = expense.category.name if expense.category else 'Uncategorized'
        category_totals[category_name] += expense.cost or 0
        
        payment_name = expense.payment_method.name if expense.payment_method else 'Unknown'
        payment_totals[payment_name] += expense.cost or 0
    
    # Category breakdown table
    if include_category_breakdown and category_totals:
        elements.append(Paragraph("Expenses by Category", heading_style))
        category_data = [['Category', 'Amount', 'Percentage']]
        total = sum(category_totals.values())
        for cat, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total * 100) if total > 0 else 0
            category_data.append([cat, f"${amount:,.2f}", f"{percentage:.1f}%"])
        
        category_table = Table(category_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(category_table)
        elements.append(Spacer(1, 0.5*inch))
    
    # Payment method breakdown table
    if include_payment_breakdown and payment_totals:
        elements.append(Paragraph("Payment Method Breakdown", heading_style))
        payment_data = [['Payment Method', 'Amount', 'Percentage']]
        total = sum(payment_totals.values())
        for method, amount in sorted(payment_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total * 100) if total > 0 else 0
            payment_data.append([method, f"${amount:,.2f}", f"{percentage:.1f}%"])
        
        payment_table = Table(payment_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 0.5*inch))
    
    # Monthly trend table
    if include_monthly_trend:
        monthly_data = calculate_monthly_breakdown(expenses)
        if monthly_data:
            elements.append(Paragraph("Monthly Spending Breakdown", heading_style))
            monthly_table_data = [['Month', 'Total Spent']]
            for month, amount in sorted(monthly_data.items()):
                monthly_table_data.append([month, f"${amount:,.2f}"])
            
            monthly_table = Table(monthly_table_data, colWidths=[3*inch, 2*inch])
            monthly_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            elements.append(monthly_table)
            elements.append(Spacer(1, 0.5*inch))
    
    # Add page break before charts if we have any
    if (include_pie_chart or include_bar_chart or include_trend_chart) and (include_summary or include_category_breakdown or include_payment_breakdown or include_monthly_trend):
        elements.append(PageBreak())
    
    # Charts section
    if include_pie_chart or include_bar_chart or include_trend_chart:
        elements.append(Paragraph("Visual Analytics", heading_style))
        elements.append(Spacer(1, 0.25*inch))
    
    # Category pie chart
    if include_pie_chart and category_totals:
        pie_chart = create_pie_chart(dict(category_totals), "Expense Categories")
        if pie_chart:
            elements.append(pie_chart)
            elements.append(Spacer(1, 0.5*inch))
    
    # Payment method bar chart
    if include_bar_chart and payment_totals:
        bar_chart = create_bar_chart(dict(payment_totals), "Payment Methods Used")
        if bar_chart:
            elements.append(bar_chart)
            elements.append(Spacer(1, 0.5*inch))
    
    # Spending trend chart
    if include_trend_chart and expenses:
        trend_chart = create_trend_chart(expenses, "Monthly Spending Trend")
        if trend_chart:
            elements.append(trend_chart)
            elements.append(Spacer(1, 0.5*inch))
    
    # Add page break before expense table if we have charts
    if (include_pie_chart or include_bar_chart or include_trend_chart) and include_expense_table:
        elements.append(PageBreak())
    
    # Detailed expense list
    if include_expense_table and expenses:
        elements.append(Paragraph("Detailed Expense List", heading_style))
        
        # Build column headers based on selected options
        headers = ['Date', 'Title']
        col_widths = [1*inch, 1.8*inch]
        
        if include_descriptions:
            headers.append('Description')
            col_widths.append(1.5*inch)
        
        headers.append('Category')
        col_widths.append(1.2*inch)
        headers.append('Amount')
        col_widths.append(0.9*inch)
        headers.append('Payment')
        col_widths.append(1.1*inch)
        
        if include_locations:
            headers.append('Location/Vendor')
            col_widths.append(1.3*inch)
        
        if include_notes:
            headers.append('Notes')
            col_widths.append(1.5*inch)
        
        # Adjust column widths to fit page
        total_width = sum(col_widths)
        if total_width > 7.5*inch:
            scale_factor = 7.5*inch / total_width
            col_widths = [w * scale_factor for w in col_widths]
        
        expense_data = [headers]
        
        for expense in expenses:
            row = [
                expense.date.strftime('%m/%d/%Y') if expense.date else 'N/A',
                (expense.title or 'Untitled')[:30]
            ]
            
            if include_descriptions:
                desc = (expense.description or '')[:40]
                if len(expense.description or '') > 40:
                    desc += '...'
                row.append(desc)
            
            row.append(expense.category.name if expense.category else 'N/A')
            row.append(f"${expense.cost:,.2f}" if expense.cost else '$0.00')
            row.append(expense.payment_method.name[:15] if expense.payment_method else 'N/A')
            
            if include_locations:
                location = expense.location or expense.vendor or 'N/A'
                row.append(location[:20])
            
            if include_notes:
                notes = (expense.notes or '')[:30]
                if len(expense.notes or '') > 30:
                    notes += '...'
                row.append(notes)
            
            expense_data.append(row)
        
        expense_table = Table(expense_data, colWidths=col_widths)
        expense_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        # Find amount column and right-align it
        amount_col = headers.index('Amount')
        expense_table.setStyle(TableStyle([
            ('ALIGN', (amount_col, 1), (amount_col, -1), 'RIGHT'),
        ]))
        
        elements.append(expense_table)
    
    # Build PDF
    doc.build(elements)
    
    # Rewind the buffer
    buffer.seek(0)
    
    # Generate filename with timestamp
    filename = f"pcs_expense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 16MB.', 'danger')
    return redirect(url_for('new_expense'))

def initialize_app():
    """Initialize the application, create directories and database"""
    # Import here to avoid circular dependencies
    from db_init import run_auto_migration, initialize_database
    
    # Create directories before database initialization
    basedir = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(os.path.join(basedir, 'data'), exist_ok=True)
    os.makedirs(os.path.join(basedir, 'uploads'), exist_ok=True)
    
    # Run automatic database migration first
    print("Starting automatic database migration...")
    if run_auto_migration():
        print("Database migration completed successfully")
    else:
        print("Warning: Database migration encountered issues")
    
    # Create tables and initialize data
    with app.app_context():
        db.create_all()
        # Use db_init's initialization which includes version tracking
        initialize_database(app, db)

# Initialize on import for gunicorn
initialize_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)