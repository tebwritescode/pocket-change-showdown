# Pocket Change Showdown

> Track every penny of your moving expenses with style! 💰

<div align="center">

![PCS Logo](https://teb.codes/2-Code/Flask/Pcs/logo.png)


![Flask](https://img.shields.io/badge/Flask-2.3.3-000000?style=for-the-badge&logo=flask)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![License](https://img.shields.io/badge/License-MIT?style=for-the-badge&logo=MIT&label=MIT)

[Features](#features) • [Quick Start](#quick-start) • [Installation](#installation) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## 📋 Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Quick Start](#quick-start)
- [Installation](#installation)
  - [Docker](#docker)
  - [Kubernetes](#kubernetes)
  - [Local Development](#local-development)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Functionality
- 📸 **Receipt Management** - Upload and store receipt images/PDFs (up to 16MB)
- 💳 **Multiple Payment Methods** - Track how you paid (Cash, Credit, Debit, etc.)
- 🏷️ **Smart Categorization** - Pre-defined PCS categories (Moving, Travel, Housing, etc.)
- 📊 **Analytics Dashboard** - Interactive charts with Chart.js
- 🎨 **8 Color Themes** - Personalize your experience
- 📱 **Mobile Responsive** - Track expenses on the go
- 🔒 **No Login Required** - Simple, secure, and private

### Data Management
- 📥 **CSV Import** - Bulk upload expenses from spreadsheets
- 📤 **CSV Export** - Download all data for records
- 📄 **Template Download** - Get started with the right format
- 💾 **Persistent Storage** - Data survives container restarts

### PCS-Specific Categories
- 🚚 Moving
- ✈️ Travel  
- 🏠 Housing
- 📦 Storage
- 🚗 Transportation
- 🏨 Lodging
- 🍔 Food
- 📦 Supplies
- 🛎️ Services
- ➕ Custom Categories

## 📸 Screenshots

<details>
<summary>Click to view screenshots</summary>

### Dashboard
Interactive analytics with spending trends and category breakdowns.

### Expense Entry
Simple form with receipt upload and auto-complete fields.

### Settings
Manage categories, payment methods, and themes.

</details>

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Pull and run the latest image
docker run -d \
  --name pcs-tracker \
  -p 5001:5001 \
  -v pcs-data:/app/data \
  -v pcs-uploads:/app/uploads \
  tebwritescode/pocket-change-showdown:latest

# Access at http://localhost:5001
```

### Docker Compose

```bash
# Clone the repository
git clone https://github.com/tebwritescode/pocket-change-showdown.git
cd pocket-change-showdown

# Start with Docker Compose
docker-compose up -d

# Access at http://localhost:5001
```

## 📦 Installation

### Docker

#### Multi-Architecture Support
Images are available for:
- `linux/amd64` (Intel/AMD)
- `linux/arm64` (Apple Silicon, ARM servers)
- `linux/arm/v7` (Raspberry Pi)

```bash
# Pull specific architecture
docker pull --platform linux/arm64 tebwritescode/pocket-change-showdown:latest

# Or let Docker auto-select
docker pull tebwritescode/pocket-change-showdown:latest
```

#### Docker Run Options

```bash
# Basic deployment
docker run -d \
  --name pcs-tracker \
  -p 5001:5001 \
  tebwritescode/pocket-change-showdown:latest

# With persistent storage
docker run -d \
  --name pcs-tracker \
  -p 5001:5001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/uploads:/app/uploads \
  tebwritescode/pocket-change-showdown:latest

# With environment variables
docker run -d \
  --name pcs-tracker \
  -p 5001:5001 \
  -e SECRET_KEY="your-secret-key-here" \
  -e FLASK_ENV="production" \
  -v pcs-data:/app/data \
  -v pcs-uploads:/app/uploads \
  tebwritescode/pocket-change-showdown:latest
```

### Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml  # Optional

# Check deployment status
kubectl get all -n pcs-tracker

# Access via NodePort (default: 30001)
http://<node-ip>:30001
```

#### Kubernetes Features
- **Persistent Volumes** - Data and uploads stored in PVCs
- **Health Checks** - Liveness and readiness probes
- **Resource Limits** - CPU and memory constraints
- **Multi-Service** - LoadBalancer and NodePort options
- **Ingress Ready** - Configure for your domain

### Local Development

```bash
# Clone repository
git clone https://github.com/tebwritescode/pocket-change-showdown.git
cd pocket-change-showdown

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Access at http://localhost:5001
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `pcs-secret-key-2024` |
| `FLASK_ENV` | Environment mode (`development`/`production`) | `production` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///data/pcs_tracker.db` |
| `MAX_CONTENT_LENGTH` | Maximum upload size in bytes | `16777216` (16MB) |

### Data Persistence

The application stores data in two locations:
- `/app/data` - SQLite database
- `/app/uploads` - Receipt images (stored in database as BLOB)

Mount these directories as volumes to persist data.

## 📱 Usage

### Adding Expenses

1. Click **"Add Expense"** from the navigation or homepage
2. Fill in expense details (only title is truly required)
3. Upload receipt photo/screenshot (optional)
4. Save expense

### Importing Data

1. Navigate to **Import/Export** → **Import CSV**
2. Download the template for correct format
3. Fill in your data
4. Upload CSV file

### CSV Format

```csv
Date,Title,Description,Category,Cost,Payment Method,Location,Vendor,Notes,Tags
2024-01-15,Moving Truck,U-Haul rental,Moving,299.99,Credit Card,Downtown,U-Haul,26ft truck,moving
2024-01-16,Hotel Stay,Overnight stay,Lodging,125.00,Company Card,Holiday Inn,Holiday Inn,1 night,travel
```

### Managing Categories & Payment Methods

1. Go to **Settings**
2. Add custom categories with colors
3. Add custom payment methods
4. Delete non-default items
5. Change color theme

### Analytics Dashboard

- Filter by time period (Week/Month/Quarter/Year)
- View spending by category (Doughnut chart)
- Payment method breakdown (Bar chart)
- Daily spending trends (Line chart)
- Top categories table with percentages

## 🔌 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Homepage with statistics |
| GET | `/expenses` | List all expenses |
| GET/POST | `/expense/new` | Add new expense |
| GET/POST | `/expense/<id>/edit` | Edit expense |
| POST | `/expense/<id>/delete` | Delete expense |
| GET | `/expense/<id>/receipt` | View receipt image |
| GET | `/dashboard` | Analytics dashboard |
| GET | `/api/expense_data` | JSON data for charts |
| GET/POST | `/settings` | Application settings |
| POST | `/settings/category/add` | Add category |
| POST | `/settings/payment/add` | Add payment method |
| GET | `/export` | Export CSV |
| GET/POST | `/import` | Import CSV |
| GET | `/template` | Download CSV template |

### API Response Example

```json
GET /api/expense_data?period=month

{
  "categories": {
    "labels": ["Moving", "Travel", "Housing"],
    "data": [1250.50, 890.25, 2100.00]
  },
  "payment_methods": {
    "labels": ["Credit Card", "Cash", "Company Card"],
    "data": [3500.75, 450.00, 290.00]
  },
  "daily_trend": {
    "labels": ["2024-01-01", "2024-01-02"],
    "data": [125.50, 340.25]
  }
}
```

## 🛠️ Development

### Tech Stack

- **Backend**: Flask 2.3.3, SQLAlchemy
- **Frontend**: Bootstrap 5, Chart.js, Font Awesome
- **Database**: SQLite with SQLAlchemy ORM
- **File Storage**: Binary storage in database
- **Deployment**: Docker, Kubernetes, Gunicorn

### Project Structure

```
pocket-change-showdown/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Multi-arch Docker build
├── docker-compose.yml    # Docker Compose config
├── templates/            # HTML templates
│   ├── base.html        # Base template with themes
│   ├── index.html       # Homepage
│   ├── expenses.html    # Expense list
│   ├── expense_form.html # Add/Edit form
│   ├── dashboard.html   # Analytics
│   ├── settings.html    # Settings page
│   └── import.html      # CSV import
├── k8s/                  # Kubernetes manifests
│   ├── namespace.yaml
│   ├── secret.yaml
│   ├── pvc.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── data/                 # Database (created at runtime)
```

### Building from Source

```bash
# Build Docker image
docker build -t pcs-tracker .

# Build multi-arch with buildx
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t tebwritescode/pocket-change-showdown:latest \
  --push .
```

### Database Schema

```sql
-- Main expense table
CREATE TABLE expense (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200),
    description TEXT,
    category_id INTEGER REFERENCES category(id),
    cost FLOAT DEFAULT 0.0,
    payment_method_id INTEGER REFERENCES payment_method(id),
    date DATE,
    receipt_image BLOB,
    receipt_filename VARCHAR(200),
    location VARCHAR(200),
    vendor VARCHAR(200),
    notes TEXT,
    tags VARCHAR(500),
    created_at DATETIME,
    updated_at DATETIME
);

-- Categories table
CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#0d6efd',
    icon VARCHAR(50) DEFAULT 'fa-tag',
    is_default BOOLEAN DEFAULT FALSE
);

-- Payment methods table
CREATE TABLE payment_method (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    icon VARCHAR(50) DEFAULT 'fa-credit-card',
    is_default BOOLEAN DEFAULT FALSE
);

-- Settings table
CREATE TABLE settings (
    id INTEGER PRIMARY KEY,
    color_scheme VARCHAR(50) DEFAULT 'default',
    default_view VARCHAR(20) DEFAULT 'list'
);
```

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with Flask and Bootstrap
- Charts powered by Chart.js
- Icons by Font Awesome

## Support

Issues? Questions? Praise-singing?  
File an issue on GitHub or yell at [teb](https://github.com/tebwritescode).

---
👑 Created by: [tebbydog0605](https://github.com/tebwritescode)  
🐋 Docker Hub: [tebwritescode](https://hub.docker.com/u/tebwritescode)  
💻 Website: [teb.codes](https://teb.codes)
