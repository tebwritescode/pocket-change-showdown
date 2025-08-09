"""
PDF generation utilities with chart creation
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import Image
from collections import defaultdict
from datetime import datetime, timedelta
import calendar

def create_pie_chart(data_dict, title="Category Breakdown"):
    """Create a pie chart and return it as a ReportLab Image"""
    if not data_dict:
        return None
    
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Sort data by value
    sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
    labels = [f"{k}\n${v:,.0f}" for k, v in sorted_data[:8]]  # Top 8 categories
    values = [v for k, v in sorted_data[:8]]
    
    # If there are more than 8 categories, group the rest as "Other"
    if len(sorted_data) > 8:
        other_total = sum(v for k, v in sorted_data[8:])
        labels.append(f"Other\n${other_total:,.0f}")
        values.append(other_total)
    
    # Create pie chart with PCS colors
    colors_list = ['#0d6efd', '#28a745', '#dc3545', '#ffc107', '#17a2b8', 
                   '#6f42c1', '#fd7e14', '#20c997', '#e83e8c', '#6c757d']
    
    wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                       colors=colors_list[:len(values)],
                                       startangle=90)
    
    # Enhance text
    for text in texts:
        text.set_fontsize(9)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(8)
        autotext.set_weight('bold')
    
    ax.set_title(title, fontsize=12, fontweight='bold', color='#0d6efd')
    
    # Save to BytesIO
    img_buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    
    img_buffer.seek(0)
    return Image(img_buffer, width=4*72, height=4*72)  # 4 inches square

def create_bar_chart(data_dict, title="Payment Methods", xlabel="", ylabel="Amount ($)"):
    """Create a bar chart and return it as a ReportLab Image"""
    if not data_dict:
        return None
    
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Sort and prepare data
    sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
    categories = [k for k, v in sorted_data]
    values = [v for k, v in sorted_data]
    
    # Create bar chart
    bars = ax.bar(categories, values, color='#0d6efd', edgecolor='#0a58ca', linewidth=1)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'${value:,.0f}',
                ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=12, fontweight='bold', color='#0d6efd')
    
    # Rotate x labels if many categories
    if len(categories) > 5:
        plt.xticks(rotation=45, ha='right')
    
    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Save to BytesIO
    img_buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    
    img_buffer.seek(0)
    return Image(img_buffer, width=5.5*72, height=3*72)  # 5.5 x 3 inches

def create_trend_chart(expenses, title="Spending Trend"):
    """Create a line chart showing spending over time"""
    if not expenses:
        return None
    
    # Group expenses by month
    monthly_data = defaultdict(float)
    for expense in expenses:
        if expense.date:
            month_key = expense.date.strftime('%Y-%m')
            monthly_data[month_key] += expense.cost or 0
    
    if not monthly_data:
        return None
    
    # Sort by date
    sorted_months = sorted(monthly_data.items())
    
    # Prepare data
    months = []
    values = []
    for month_str, value in sorted_months:
        year, month = month_str.split('-')
        months.append(f"{calendar.month_abbr[int(month)]} {year[-2:]}")
        values.append(value)
    
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Create line chart with markers
    ax.plot(months, values, color='#0d6efd', linewidth=2, marker='o', 
            markersize=6, markerfacecolor='white', markeredgecolor='#0d6efd', 
            markeredgewidth=2)
    
    # Fill area under line
    ax.fill_between(range(len(months)), values, alpha=0.2, color='#0d6efd')
    
    # Add value labels
    for i, (month, value) in enumerate(zip(months, values)):
        ax.text(i, value, f'${value:,.0f}', ha='center', va='bottom', fontsize=8)
    
    ax.set_xlabel('Month', fontsize=10)
    ax.set_ylabel('Total Spending ($)', fontsize=10)
    ax.set_title(title, fontsize=12, fontweight='bold', color='#0d6efd')
    
    # Rotate x labels if many months
    if len(months) > 6:
        plt.xticks(rotation=45, ha='right')
    
    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.xaxis.grid(True, linestyle='--', alpha=0.1)
    ax.set_axisbelow(True)
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Save to BytesIO
    img_buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    
    img_buffer.seek(0)
    return Image(img_buffer, width=5.5*72, height=3*72)  # 5.5 x 3 inches

def calculate_monthly_breakdown(expenses):
    """Calculate monthly spending breakdown"""
    monthly_data = defaultdict(float)
    for expense in expenses:
        if expense.date:
            month_key = expense.date.strftime('%B %Y')
            monthly_data[month_key] += expense.cost or 0
    return dict(monthly_data)