#!/bin/bash
# KPI Operations System - Deployment Script

echo "🏭 KPI Operations System - Production Deployment"
echo "================================================"

# Check Python version
echo "✅ Checking Python version..."
python --version

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM DEPENDENCIES FOR WEASYPRINT (PDF generation)
# WeasyPrint requires GTK3 / Pango / Cairo / GObject libraries at the OS level.
# These are NOT Python packages — they must be installed via the system package
# manager BEFORE `pip install weasyprint` will work correctly.
# Without them, PDF downloads will silently fail on the production server even
# though they work fine on a local Windows machine (which ships GTK via the
# weasyprint Windows wheel).
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "📦 Installing WeasyPrint system dependencies (GTK3 / Pango / Cairo)..."

if command -v apt-get &>/dev/null; then
    # ── Debian / Ubuntu ──────────────────────────────────────────────────────
    echo "   Detected: Debian/Ubuntu (apt-get)"
    sudo apt-get update -y
    sudo apt-get install -y \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libcairo-gobject2 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
        fonts-liberation \
        fonts-dejavu-core \
        python3-dev \
        python3-pip \
        gcc
    echo "   ✅ Debian/Ubuntu system packages installed."

elif command -v yum &>/dev/null; then
    # ── RHEL / CentOS / Amazon Linux ─────────────────────────────────────────
    echo "   Detected: RHEL/CentOS/Amazon Linux (yum)"
    sudo yum install -y \
        pango \
        cairo \
        cairo-gobject \
        gdk-pixbuf2 \
        libffi-devel \
        python3-devel \
        gcc
    echo "   ✅ RHEL/CentOS system packages installed."

elif command -v dnf &>/dev/null; then
    # ── Fedora / newer RHEL ──────────────────────────────────────────────────
    echo "   Detected: Fedora/RHEL8+ (dnf)"
    sudo dnf install -y \
        pango \
        cairo \
        cairo-gobject \
        gdk-pixbuf2 \
        libffi-devel \
        python3-devel \
        gcc
    echo "   ✅ Fedora/RHEL8+ system packages installed."

elif command -v apk &>/dev/null; then
    # ── Alpine Linux (Docker) ────────────────────────────────────────────────
    echo "   Detected: Alpine Linux (apk)"
    apk add --no-cache \
        pango \
        cairo \
        gdk-pixbuf \
        libffi-dev \
        musl-dev \
        gcc \
        ttf-dejavu
    echo "   ✅ Alpine system packages installed."

else
    echo "   ⚠️  Could not detect package manager."
    echo "   Please install WeasyPrint system dependencies manually."
    echo "   See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
fi

echo ""

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

# Verify WeasyPrint can import correctly
echo ""
echo "🔍 Verifying WeasyPrint installation..."
python -c "
import sys
try:
    import weasyprint
    print('   ✅ WeasyPrint imported successfully — version:', weasyprint.__version__)
    # Quick smoke-test: render a tiny HTML snippet to PDF
    from io import BytesIO
    buf = BytesIO()
    weasyprint.HTML(string='<p>test</p>').write_pdf(buf)
    print('   ✅ WeasyPrint PDF render test PASSED — PDF downloads will work.')
except Exception as e:
    print('   ❌ WeasyPrint test FAILED:', e)
    print('   PDF downloads will fall back to xhtml2pdf.')
    print('   Run: sudo apt-get install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0')
    sys.exit(0)  # Non-fatal — fallback renderer is available
"
echo ""

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