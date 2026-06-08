#!/usr/bin/env python
"""
Security and Compliance Enhancement Installation Script
Installs required packages and runs migrations for audit trails
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and print status"""
    print(f"\n{'='*60}")
    print(f"⏳ {description}...")
    print(f"{'='*60}")
    result = subprocess.run(command, shell=True, capture_output=False)
    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
    else:
        print(f"❌ {description} - FAILED")
        sys.exit(1)

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  KPI Operations System - Security Enhancement Installer   ║
    ║                                                            ║
    ║  This script will install:                                ║
    ║  ✓ django-simple-history (Immutable audit trails)        ║
    ║  ✓ django-axes (Brute force protection)                  ║
    ║  ✓ drf-spectacular (API documentation)                   ║
    ║  ✓ django-ratelimit (Rate limiting)                      ║
    ║  ✓ django-environ (Environment configuration)            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("\n⚠️  WARNING: You don't appear to be in a virtual environment!")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            sys.exit(0)
    
    # Step 1: Install required packages
    run_command(
        "pip install django-simple-history==3.4.0 django-axes==6.1.1 drf-spectacular==0.27.0 django-ratelimit==4.1.0 django-environ==0.11.2",
        "Installing security packages"
    )
    
    # Step 2: Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        print("\n⏳ Creating .env file...")
        with open('.env', 'w') as f:
            f.write("""# Django Security Settings
SECRET_KEY=change-this-to-a-random-50-character-string-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Two-Factor Authentication
USE_2FA=False

# Session Settings
SESSION_COOKIE_AGE=86400
""")
        print("✅ Created .env file (REMEMBER TO UPDATE SECRET_KEY!)")
    else:
        print("\n✅ .env file already exists")
    
    # Step 3: Run migrations for audit trail tables
    run_command(
        "python manage.py makemigrations",
        "Creating migrations for audit trails"
    )
    
    run_command(
        "python manage.py migrate",
        "Running database migrations"
    )
    
    # Step 4: Collect static files
    run_command(
        "python manage.py collectstatic --noinput",
        "Collecting static files"
    )
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║              ✅ INSTALLATION COMPLETE!                    ║
    ╚════════════════════════════════════════════════════════════╝
    
    🎉 Security enhancements successfully installed!
    
    📝 NEXT STEPS:
    
    1. Update SECRET_KEY in .env file:
       - Generate a random 50+ character string
       - Keep it secret and secure
    
    2. Configure production settings in .env:
       - Set DEBUG=False for production
       - Update ALLOWED_HOSTS with your domain
    
    3. Test brute force protection:
       - Try logging in with wrong password 5 times
       - Account should lock for 1 hour
    
    4. View API documentation:
       - Start server: python manage.py runserver
       - Visit: http://127.0.0.1:8000/api/docs/
    
    5. Check audit trails:
       - Edit any BMR record in admin
       - View history in admin interface
    
    6. Review security settings:
       - Check kampala_pharma/settings.py
       - Verify all security middleware enabled
    
    ⚠️  SECURITY REMINDERS:
    - Never commit .env file to git
    - Change SECRET_KEY before production
    - Set DEBUG=False in production
    - Enable 2FA for admin users
    - Regular security audits recommended
    
    📚 Documentation:
    - Audit Trails: http://127.0.0.1:8000/admin/ (view history)
    - API Docs: http://127.0.0.1:8000/api/docs/
    - Locked Accounts: http://127.0.0.1:8000/admin/axes/
    
    """)

if __name__ == '__main__':
    main()
