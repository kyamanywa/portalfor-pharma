# KPI Operations System - Admin Guide
## Dashboard Permissions, Django Groups, and Security Features

**Note**: This is a technical reference guide. The final user guide will be created separately with step-by-step instructions and screenshots.

---

## Table of Contents
1. [Dashboard Permission System](#1-dashboard-permission-system)
2. [Django Groups (Not Currently Implemented)](#2-django-groups-not-currently-implemented)
3. [OTP/TOTP Two-Factor Authentication](#3-otptotp-two-factor-authentication)
4. [User Role Management](#4-user-role-management)

---

## 1. Dashboard Permission System

### Overview
The system uses a **custom permission model** (`DashboardPermission`) instead of Django's built-in permissions. This provides more flexible, role-based dashboard access control.

### How It Works

**Location**: `dashboards/models.py` → `DashboardPermission` model

The system checks permissions in this order:
1. **Is the dashboard active?** (`is_active=True`)
2. **Is user blocked?** (Check `blocked_users`)
3. **Is user specifically allowed?** (Check `allowed_users`)
4. **System permissions** (Check `requires_superuser`, `requires_staff`)
5. **Role permissions** (Check if user's role is in `allowed_roles`)

### Controlling Dashboard Access via Django Admin

#### To Remove System Health from Admin Panel:

1. **Login to Django Admin**: `http://192.168.1.244:8000/admin/`

2. **Navigate to Dashboard Permissions**:
   - Go to: **Dashboards** → **Dashboard Permissions**

3. **Find "System Health" Permission**:
   - Click on "System Health" in the list

4. **Modify Access**:
   
   **Option A - Completely Disable:**
   ```
   ✅ Active: [UNCHECK THIS]
   ```
   
   **Option B - Remove from Specific Roles:**
   ```
   Allowed roles: ["qa", "production_manager"]  
   # Remove "admin" or any role you want to block
   ```
   
   **Option C - Block Specific Users:**
   ```
   Blocked users: [SELECT USERS TO BLOCK]
   ```
   
   **Option D - Make Superuser-Only:**
   ```
   ✅ Requires superuser: [CHECK THIS]
   ✅ Requires staff: [CHECK THIS]
   ```

5. **Save Changes**

### Available Dashboards

Current dashboards in the system:
- `admin_dashboard` - Admin Control Center
- `system_logs` - System Logs
- `user_management` - User Management
- `machine_management` - Machine Management
- `inventory` - Inventory Management
- `quality_control` - Quality Control Management
- `system_health` - System Health Monitor
- `qa_dashboard` - QA Dashboard
- `production_manager` - Production Manager Dashboard
- `store_dashboard` - Store Dashboard
- `qc_dashboard` - QC Dashboard
- `regulatory_dashboard` - Regulatory Dashboard
- `operator_dashboard` - Operator Dashboard

### Creating New Dashboard Permissions

**Via Django Admin:**

1. Go to **Dashboards** → **Dashboard Permissions** → **Add Dashboard Permission**

2. Fill in:
   ```
   Name: [Select from dropdown]
   Description: What this dashboard does
   
   Allowed roles: ["qa", "admin", "production_manager"]
   
   Allowed users: [Specific users if needed]
   Blocked users: [Specific users to block]
   
   ☐ Requires staff
   ☐ Requires superuser
   ✅ Active
   ```

3. **Save**

### Applying Permissions in Code

**In views** (`dashboards/views.py`):

```python
from dashboards.permissions import require_dashboard_permission

@login_required
@require_dashboard_permission('system_health')
def system_health_dashboard(request):
    # View code here
    pass
```

**Note**: Currently, most dashboards have this decorator **commented out** due to a login issue fix. They use manual role checking instead.

---

## 2. Django Groups (Not Currently Implemented)

### Current State
❌ **Django's built-in Groups system is NOT being used** in this project.

### What Are Django Groups?

Django Groups are a way to categorize users and assign permissions to the entire group:

**Example Structure:**
```
Group: "Quality Assurance Team"
├── Users: qa_user1, qa_user2, qa_user3
├── Permissions:
│   ├── Can add BMR
│   ├── Can view BMR
│   ├── Can approve BMR
│   └── Can access QA Dashboard
```

### Why Not Currently Using Groups?

The system uses a **simpler role-based approach** with the `CustomUser.role` field:
- Each user has ONE role: `qa`, `production_manager`, `store_manager`, etc.
- Dashboards check this single role field
- Easier to understand for pharmaceutical operations staff

### Should You Implement Django Groups?

**Use Groups If:**
- ✅ Users need multiple roles (e.g., someone is both QA and Production Manager)
- ✅ You want granular permissions (e.g., "can approve but not create")
- ✅ You have complex permission hierarchies
- ✅ You want to use Django's built-in permission system

**Keep Current System If:**
- ✅ One role per user is sufficient
- ✅ Simple is better for your team
- ✅ You don't need fine-grained permissions

### How to Implement Django Groups (If Needed)

**Step 1: Create Groups in Django Admin**

1. Go to: `http://192.168.1.244:8000/admin/auth/group/`
2. Click **Add Group**
3. Enter:
   ```
   Name: Quality Assurance Team
   
   Permissions:
   ✅ bmr | bmr | Can add bmr
   ✅ bmr | bmr | Can view bmr
   ✅ bmr | bmr | Can change bmr
   ✅ dashboards | dashboard permission | Can view dashboard permission
   ```
4. **Save**

**Step 2: Assign Users to Groups**

1. Go to **Users** in Django Admin
2. Edit a user
3. Under **Groups**, select the groups they belong to
4. **Save**

**Step 3: Check Group Permissions in Code**

```python
# In views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin

@login_required
def create_bmr(request):
    # Check if user is in "Quality Assurance Team" group
    if request.user.groups.filter(name='Quality Assurance Team').exists():
        # Allow access
        pass
    else:
        # Deny access
        return HttpResponseForbidden("Access denied")

# Or using Django's built-in permission decorator
from django.contrib.auth.decorators import permission_required

@login_required
@permission_required('bmr.add_bmr', raise_exception=True)
def create_bmr(request):
    # Only users with 'add_bmr' permission can access
    pass
```

**Step 4: Integrate with Dashboard Permissions**

Modify `dashboards/models.py` → `DashboardPermission.user_has_access()`:

```python
def user_has_access(self, user):
    """Check if a user has access to this dashboard"""
    if not self.is_active:
        return False
        
    # ... existing checks ...
    
    # NEW: Check if user belongs to allowed groups
    if self.allowed_groups.exists():
        user_groups = user.groups.all()
        if self.allowed_groups.filter(id__in=user_groups).exists():
            return True
    
    # ... rest of checks ...
```

---

## 3. OTP/TOTP Two-Factor Authentication

### Current State
❌ **2FA is NOT implemented** in this system.

### What is OTP/TOTP?

**OTP** (One-Time Password): Temporary code sent via SMS/Email
**TOTP** (Time-based OTP): Code generated by authenticator app (Google Authenticator, Authy)

**How it works:**
1. User enters username/password ✅
2. System asks for 6-digit code ⏳
3. User enters code from authenticator app ✅
4. Login successful 🎉

### Why Implement 2FA?

**Benefits:**
- ✅ **Security**: Even if password is stolen, attacker needs the 2FA code
- ✅ **Compliance**: Pharmaceutical regulations often require 2FA
- ✅ **Audit Trail**: Know exactly who logged in and when
- ✅ **Prevent Unauthorized Access**: Especially important for production systems

**Use Cases in KPI:**
- Regulatory users approving BMRs
- QA users creating/approving batches
- Admin users accessing system settings
- Store managers dispensing materials

### How to Implement TOTP (Recommended)

#### Requirements

**Python Package:**
```bash
pip install django-otp qrcode[pil]
```

**Why django-otp?**
- ✅ Official Django package
- ✅ Works with Google Authenticator, Authy, Microsoft Authenticator
- ✅ Well-documented and maintained
- ✅ Integrates with Django Admin

#### Implementation Steps

**Step 1: Install Package**

```powershell
# On both dev and production
cd C:\Users\regan\Desktop\portalfor-pharma-main
venv\Scripts\activate
pip install django-otp qrcode[pil]
pip freeze > requirements.txt
```

**Step 2: Update `kampala_pharma/settings.py`**

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 2FA Apps (ADD THESE)
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',  # Backup codes
    
    # Your apps
    'accounts',
    'bmr',
    # ... rest
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # 2FA Middleware (ADD THIS - AFTER AuthenticationMiddleware)
    'django_otp.middleware.OTPMiddleware',
    
    'django.contrib.messages.middleware.MessageMiddleware',
    # ... rest
]
```

**Step 3: Run Migrations**

```powershell
python manage.py migrate
```

This creates tables:
- `otp_totp_totpdevice` - Stores user's TOTP devices
- `otp_static_staticdevice` - Backup recovery codes

**Step 4: Create 2FA Setup View** (`accounts/views.py`)

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.util import random_hex
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64

@login_required
def setup_2fa(request):
    """Setup TOTP 2FA for user"""
    user = request.user
    
    # Check if user already has 2FA
    device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    
    if request.method == 'POST':
        token = request.POST.get('token')
        
        # Get unconfirmed device
        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
        
        if device and device.verify_token(token):
            device.confirmed = True
            device.save()
            messages.success(request, '2FA successfully enabled!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Invalid code. Please try again.')
    
    # Create new device if none exists
    if not device:
        device = TOTPDevice.objects.create(
            user=user,
            name=f"{user.username}'s Device",
            confirmed=False
        )
    
    # Generate QR code
    url = device.config_url
    qr = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)
    stream = BytesIO()
    qr.save(stream)
    qr_code = base64.b64encode(stream.getvalue()).decode()
    
    return render(request, 'accounts/setup_2fa.html', {
        'qr_code': qr_code,
        'secret_key': device.key,
        'device': device
    })

@login_required
def verify_2fa(request):
    """Verify 2FA code during login"""
    if request.method == 'POST':
        token = request.POST.get('token')
        
        # Get user's device
        device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
        
        if device and device.verify_token(token):
            # Mark session as verified
            request.session['otp_verified'] = True
            return redirect('home')
        else:
            messages.error(request, 'Invalid 2FA code')
    
    return render(request, 'accounts/verify_2fa.html')

@login_required
def disable_2fa(request):
    """Disable 2FA for user"""
    if request.method == 'POST':
        TOTPDevice.objects.filter(user=request.user).delete()
        messages.success(request, '2FA has been disabled')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/disable_2fa.html')
```

**Step 5: Create Templates**

`templates/accounts/setup_2fa.html`:
```html
{% extends 'base.html' %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h4><i class="fas fa-shield-alt"></i> Setup Two-Factor Authentication</h4>
            </div>
            <div class="card-body">
                <h5>Step 1: Download Authenticator App</h5>
                <p>Install one of these apps on your phone:</p>
                <ul>
                    <li>Google Authenticator (Android/iOS)</li>
                    <li>Microsoft Authenticator (Android/iOS)</li>
                    <li>Authy (Android/iOS/Desktop)</li>
                </ul>
                
                <hr>
                
                <h5>Step 2: Scan QR Code</h5>
                <div class="text-center mb-3">
                    <img src="data:image/svg+xml;base64,{{ qr_code }}" alt="QR Code" style="width: 250px; height: 250px;">
                </div>
                
                <p class="text-center text-muted">
                    <small>Or enter this code manually: <code>{{ secret_key }}</code></small>
                </p>
                
                <hr>
                
                <h5>Step 3: Enter 6-Digit Code</h5>
                <form method="post">
                    {% csrf_token %}
                    <div class="mb-3">
                        <input type="text" name="token" class="form-control text-center" 
                               placeholder="000000" maxlength="6" required 
                               style="font-size: 24px; letter-spacing: 10px;">
                    </div>
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-check"></i> Verify and Enable 2FA
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

`templates/accounts/verify_2fa.html`:
```html
{% extends 'base.html' %}

{% block content %}
<div class="row justify-content-center mt-5">
    <div class="col-md-4">
        <div class="card">
            <div class="card-header bg-warning">
                <h4><i class="fas fa-lock"></i> Two-Factor Authentication</h4>
            </div>
            <div class="card-body">
                <p>Enter the 6-digit code from your authenticator app:</p>
                
                <form method="post">
                    {% csrf_token %}
                    <div class="mb-3">
                        <input type="text" name="token" class="form-control text-center" 
                               placeholder="000000" maxlength="6" required 
                               style="font-size: 32px; letter-spacing: 15px;" 
                               autofocus>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-sign-in-alt"></i> Verify Code
                    </button>
                </form>
                
                <hr>
                
                <p class="text-muted text-center mb-0">
                    <small>Lost your device? Contact your administrator</small>
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 6: Update URLs** (`accounts/urls.py`)

```python
urlpatterns = [
    # ... existing urls ...
    path('setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
]
```

**Step 7: Enforce 2FA on Login**

Modify `accounts/views.py` login view:

```python
from django_otp.plugins.otp_totp.models import TOTPDevice

def login_view(request):
    # ... existing login code ...
    
    if user is not None:
        # Check if user has 2FA enabled
        has_2fa = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        
        if has_2fa:
            # Store user ID in session (not fully logged in yet)
            request.session['pre_2fa_user_id'] = user.id
            return redirect('accounts:verify_2fa')
        else:
            # Normal login without 2FA
            login(request, user)
            return redirect('home')
```

**Step 8: Add 2FA Middleware (Optional)**

Create `accounts/middleware/enforce_2fa.py`:

```python
from django.shortcuts import redirect
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

class Enforce2FAMiddleware:
    """Redirect to 2FA verification if user has it enabled but hasn't verified"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Allow these URLs without 2FA
        allowed_urls = [
            reverse('accounts:login'),
            reverse('accounts:logout'),
            reverse('accounts:verify_2fa'),
            reverse('accounts:setup_2fa'),
        ]
        
        if request.user.is_authenticated and request.path not in allowed_urls:
            # Check if user has 2FA
            has_2fa = TOTPDevice.objects.filter(user=request.user, confirmed=True).exists()
            
            # Check if session is verified
            is_verified = request.session.get('otp_verified', False)
            
            if has_2fa and not is_verified:
                return redirect('accounts:verify_2fa')
        
        response = self.get_response(request)
        return response
```

Add to `settings.py`:
```python
MIDDLEWARE = [
    # ... other middleware ...
    'accounts.middleware.enforce_2fa.Enforce2FAMiddleware',
]
```

#### Making 2FA Mandatory for Specific Roles

In `accounts/signals.py`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import CustomUser
from django_otp.plugins.otp_totp.models import TOTPDevice

@receiver(post_save, sender=CustomUser)
def require_2fa_for_critical_roles(sender, instance, created, **kwargs):
    """Automatically require 2FA for QA, Regulatory, and Admin users"""
    
    critical_roles = ['qa', 'regulatory', 'admin']
    
    if instance.role in critical_roles:
        # Send notification to user
        # (Implement email/notification system)
        pass
```

---

## 4. User Role Management

### Current Roles

Defined in `accounts/models.py` → `CustomUser.ROLE_CHOICES`:

```python
ROLE_CHOICES = [
    ('production_manager', 'Production Manager'),
    ('qa', 'Quality Assurance'),
    ('regulatory', 'Regulatory Affairs'),
    ('store_manager', 'Store Manager'),
    ('qc', 'Quality Control'),
    ('mixing_operator', 'Mixing Operator'),
    ('granulation_operator', 'Granulation Operator'),
    ('blending_operator', 'Blending Operator'),
    ('compression_operator', 'Compression Operator'),
    ('coating_operator', 'Coating Operator'),
    ('drying_operator', 'Drying Operator'),
    ('filling_operator', 'Filling Operator'),
    ('tube_filling_operator', 'Tube Filling Operator'),
    ('blister_packing_operator', 'Blister Packing Operator'),
    ('bulk_packing_operator', 'Bulk Packing Operator'),
    ('secondary_packaging_operator', 'Secondary Packaging Operator'),
    ('sorting_operator', 'Sorting Operator'),
    ('fgs', 'Finished Goods Store'),
    ('admin', 'Administrator'),
]
```

### Managing User Roles

**Via Django Admin:**

1. Go to **Users** → Select a user
2. Find **Role** field dropdown
3. Select new role
4. **Save**

**Via Code:**

```python
from accounts.models import CustomUser

# Change user role
user = CustomUser.objects.get(username='john_doe')
user.role = 'qa'
user.save()

# Get all QA users
qa_users = CustomUser.objects.filter(role='qa')

# Get all operators
operators = CustomUser.objects.filter(role__contains='_operator')
```

### Role-Based Dashboard Access

Edit `dashboards/models.py` → `DashboardPermission`:

```python
# Example: System Health dashboard
permission = DashboardPermission.objects.get(name='system_health')
permission.allowed_roles = ['admin']  # Only admins
permission.save()
```

---

## Summary & Recommendations

### Current System Status

| Feature | Status | Notes |
|---------|--------|-------|
| Custom Dashboard Permissions | ✅ Implemented | Working via Django Admin |
| Role-Based Access | ✅ Implemented | Simple, one role per user |
| Django Groups | ❌ Not Used | Not needed for current setup |
| 2FA (TOTP) | ❌ Not Implemented | **Recommended for production** |
| Audit Logging | ✅ Partial | BMR changes logged, expand for 2FA |

### Immediate Recommendations

1. **Enable 2FA** for critical roles (QA, Regulatory, Admin)
2. **Review Dashboard Permissions** in Django Admin - ensure they match business needs
3. **Document** who has access to what (this will be in the final user guide)
4. **Train** administrators on managing permissions

### Next Steps

1. ✅ Review this technical guide
2. ⏳ Decide: Do we implement 2FA? (Recommended: YES)
3. ⏳ Decide: Do we need Django Groups? (Recommended: NO, keep it simple)
4. ⏳ Create final user guide with screenshots and step-by-step instructions
5. ⏳ Train IT staff on permission management

---

## Questions to Answer Before Final User Guide

1. **2FA**: Should we implement it? For which roles?
2. **Dashboard Access**: Which roles should see which dashboards?
3. **System Health**: Should admins see it, or only superusers?
4. **User Guide Format**: PDF? Markdown? Both?
5. **Screenshots**: English interface or should we consider localization?

---

**Document Version**: 1.0  
**Last Updated**: December 3, 2025  
**Author**: GitHub Copilot  
**Status**: Technical Reference - Not Final User Guide
