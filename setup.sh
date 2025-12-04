#!/bin/bash
# KPI Operations System - Quick Setup Script
# This script automates the initial setup process

echo "=========================================="
echo "KPI Operations System - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version || python --version
echo ""

# Run migrations
echo "2. Running database migrations..."
python3 manage.py migrate || python manage.py migrate
echo ""

# Initialize admin settings
echo "3. Initializing system settings..."
python3 manage.py init_admin_settings || python manage.py init_admin_settings
echo ""

# Initialize dashboard permissions
echo "4. Initializing dashboard permissions..."
python3 manage.py init_dashboard_permissions || python manage.py init_dashboard_permissions
echo ""

# Seed product types
echo "5. Creating product types and workflows..."
python3 manage.py seed_product_types || python manage.py seed_product_types
echo ""

# Initialize timing settings
echo "6. Initializing phase timing settings..."
python3 manage.py init_timing_settings || python manage.py init_timing_settings
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Create a superuser: python manage.py createsuperuser"
echo "2. (Optional) Create sample users: python manage.py create_sample_users"
echo "3. Start the server: python manage.py runserver"
echo ""
echo "Access the system at: http://127.0.0.1:8000/"
echo "Admin panel at: http://127.0.0.1:8000/admin/"
echo ""
echo "For detailed documentation, see INSTALLATION_GUIDE.md"
echo "=========================================="
