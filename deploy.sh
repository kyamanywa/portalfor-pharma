#!/bin/bash
# KPI Operations System - Deployment Script

echo "🏭 KPI Operations System - Production Deployment"
echo "================================================"

# Check Python version
echo "✅ Checking Python version..."
python --version

# Create virtual environment
echo "✅ Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo "✅ Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "✅ Installing requirements..."
pip install -r requirements.txt

# Database migrations
echo "✅ Running database migrations..."
python manage.py migrate

# Initialize admin settings
echo "✅ Initializing admin settings..."
python manage.py init_admin_settings

# Initialize system defaults
echo "✅ Initializing system defaults..."
python manage.py init_system_defaults

# Collect static files (for production)
echo "✅ Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "🎯 DEPLOYMENT COMPLETE!"
echo "======================="
echo ""
echo "🚀 To start the system:"
echo "   python manage.py runserver"
echo ""
echo "🌐 Access URLs:"
echo "   Main System: http://127.0.0.1:8000/"
echo "   Admin Panel: http://127.0.0.1:8000/admin/"
echo "   API Docs: http://127.0.0.1:8000/api/v1/"
echo ""
echo "👤 Default Login:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "⚠️  Remember to:"
echo "   1. Change default passwords"
echo "   2. Configure production database"
echo "   3. Set up SSL/HTTPS"
echo "   4. Configure backup system"
echo ""
echo "📚 Documentation:"
echo "   - KPI_OPERATIONS_SYSTEM_COMPLETE_MANUAL.md"
echo "   - TIMING_CONFIGURATION_GUIDE.md"
echo "   - OPERATOR_ROLES.md"
echo ""