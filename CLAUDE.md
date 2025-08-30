# CLAUDE.md

This file provides guidance for development when working with code in this repository.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally for development
python app.py

# Docker build and run
docker-compose up -d

# Deploy to Kubernetes
./deploy.sh
```

## Architecture Overview

This is a Flask-based web application for tracking PCS (Permanent Change of Station) orders and related expenses:

### Backend Architecture
- **app.py**: Main Flask application with routes and business logic
- **pdf_utils.py**: PDF generation utilities
- SQLite database for data persistence
- Gunicorn WSGI server for production deployment

### Frontend Architecture
- Bootstrap-based UI with responsive design
- Templates in `templates/` directory
- Static assets in `static/` directory

### Deployment
- Docker container with multi-architecture support (linux/amd64, linux/arm64)
- Kubernetes deployment manifests in `k8s/` directory
- Deploy script for automated Kubernetes deployment

## Important Development Notes

**CRITICAL**: NEVER include any references to Claude, AI assistants, or automated code generation in ANY of the following:
- Git commit messages
- Code comments
- Documentation
- Console logs
- Error messages
- Build outputs
- Generated artifacts

1. **Version Management**:
   - Version is tracked in `deploy.sh` as VERSION variable
   - Format: vX.Y.Z (e.g., v2.0.0)
   - Update version before each deployment/release
   - Version is also referenced in Kubernetes manifests

2. **Docker Deployment**:
   - Multi-architecture builds supported
   - Repository: `tebwritescode/pcs-tracker`
   - Always tag with version and latest
   - Build command: `docker buildx build --platform linux/amd64,linux/arm64 -t tebwritescode/pcs-tracker:latest -t tebwritescode/pcs-tracker:v2.0.0 --push .`

3. **Environment Variables**:
   - `FLASK_APP`: Set to app.py
   - `PYTHONUNBUFFERED`: Set to 1 for proper logging

4. **Security**:
   - Application runs as non-root user (pcsuser)
   - Proper file permissions set in Dockerfile
   - Health checks configured

5. **Testing**:
   - Always test locally before pushing
   - Verify PDF generation functionality
   - Test data import/export features

6. **Git Commit Messages**:
   - Use clear, descriptive commit messages
   - Format: "Add PDF export functionality" or "Fix expense calculation bug"
   - Include version information when appropriate: "Release v2.0.1 with bug fixes"
- never just accept errors, any errors found need to be corrected before pushing