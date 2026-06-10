# Kampala Pharmaceutical Industries - Operations Management System

A comprehensive pharmaceutical production workflow management system built with Django, designed for managing the complete production lifecycle from BMR creation to finished goods storage.

## 📋 System Overview

### Core Features
- **Role-Based Access Control**: Each user type has a dedicated dashboard
- **Electronic Batch Records**: Full BMR lifecycle management
- **Real-Time Production Tracking**: Live monitoring of all production phases
- **Integrated Quality Management**: 
  - Built-in QC checkpoints with rollback capability
  - Comprehensive quarantine management
  - QA oversight and electronic approvals
- **Finished Goods Management**: Complete tracking through to storage

### Product Types & Workflows

#### 1. Ointments Production
```
BMR Creation → Regulatory Approval → Material Release → Dispensing → 
Mixing → QC Testing → Tube Filling → Packaging Release → 
Secondary Packaging → Final QA → Finished Goods
```

#### 2. Tablets Production (Normal & Type 2)
```
BMR Creation → Regulatory Approval → Material Release → Dispensing →
Granulation → Blending → Compression → QC Testing → Sorting →
[Coating (if needed)] → Packaging Release → [Blister/Bulk Packing] →
Secondary Packaging → Final QA → Finished Goods
```

#### 3. Capsules Production
```
BMR Creation → Regulatory Approval → Material Release → Dispensing →
Blending → QC Testing → Filling → Sorting →
Packaging Release → Blister Packing → Secondary Packaging →
Final QA → Finished Goods
```

## 👥 User Roles & Dashboards

### Production Management
- **Production Manager**: Production planning and BMR requests
- **QA Officers**: BMR creation and quality oversight
- **Regulatory Affairs**: Compliance and documentation review

### Material Management
- **Store Manager**: Raw material release and inventory
- **Dispensing Manager**: Material dispensing and tracking
- **Packaging Store**: Packaging material management

### Production Operations
- **Production Operators**: Phase-specific dashboards for:
  - Mixing/Granulation
  - Blending/Compression
  - Coating/Filling
  - Packaging/Packing

### Quality Management
- **QC Team**: 
  - In-process testing and verification
  - Sample analysis and documentation
  - Pass/fail determinations
  - Trend analysis and reporting
- **QA Team**:
  - BMR creation and review
  - Sample collection and handling
  - Final product approval
  - Quality system oversight
- **Quarantine Management**:
  - Non-conforming product isolation
  - Sample request processing
  - QA/QC coordination
  - Release authorization

## 🔄 Workflow Features

### BMR Management
- Manual batch numbering (format: XXX-YYYY)
- Electronic signatures for approvals
- Material requirement calculations
- In-process control specifications

### Production Control
- Automatic phase progression
- QC checkpoints with pass/fail routing
- Equipment status monitoring
- Breakdown tracking
- Production-initiated QC requests
- Real-time quality status updates

### Quality Control & Quarantine Management
- Critical QC Checkpoints:
  - Post-mixing QC testing
  - Post-blending QC verification
  - Post-compression QC analysis
- Quarantine Process Flow:
  - Batch quarantine initiation
  - Sample request management
  - QA sampling workflow
  - QC testing and verification
  - Release/reject decisions
- Quality Metrics:
  - Sample turnaround times
  - Test pass/fail rates
  - Quarantine duration tracking
  - QA/QC performance metrics
- Automated Features:
  - Phase rollback on failures
  - Electronic COA generation
  - Sample tracking system
  - Audit trail maintenance

## 🔍 Dashboard Features

### Live Tracking
- Real-time batch status
- Phase completion metrics
- Equipment utilization
- Quality Monitoring:
  - Active quarantine batches
  - Pending QA/QC samples
  - Test result status
  - Release/reject rates

### Analytics
- Production efficiency metrics
- Quality trend analysis
- Cycle time tracking
- Yield monitoring

### Reporting
- Batch manufacturing records
- Quality control reports
- Production summaries
- Regulatory documentation

## 🏗️ Technical Architecture

### Backend (Django)
- `accounts/`: User and authentication management
- `bmr/`: Batch record management
- `workflow/`: Production phase control
- `products/`: Product specifications
- `dashboards/`: User interfaces
- `reports/`: Reporting and analytics

### Security Features
- Role-based access control
- Electronic signatures
- Audit trailing
- Session management

### Database Design
- Structured for GMP compliance
- Complete audit history
- Data integrity controls
- Backup and recovery

## 🚀 Getting Started

### Prerequisites
- Python 3.8+ (Python 3.11+ recommended)
- pip (Python package manager)
- Virtual environment support
- 4GB RAM minimum (8GB+ recommended)
- 10GB free storage

### Quick Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/kyamanywa/portalfor-pharma.git
cd portalfor-pharma
```

#### 2. Create Virtual Environment
**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Initialize Database
```bash
python manage.py migrate
```

#### 5. Load Default System Data (REQUIRED)
**These commands set up essential system configurations:**

```bash
# Initialize all system settings (Dashboard, Session, Alerts, Production Limits)
python manage.py init_admin_settings

# Initialize dashboard permissions (Role-based access control)
python manage.py init_dashboard_permissions

# Create product types and workflows (Ointments, Tablets, Capsules)
python manage.py seed_product_types

# Initialize phase timing settings (Optional but recommended)
python manage.py init_timing_settings
```

**What gets created:**
- ✅ 62 configurable system settings (dashboard, session, alerts, limits)
- ✅ 15 dashboard permission controls
- ✅ 4 product types with complete production workflows
- ✅ All production phases properly configured
- ✅ Phase timing templates

#### 6. Create Admin User
```bash
python manage.py createsuperuser
```

#### 7. Create Sample Users (Optional - For Testing)
```bash
python manage.py create_sample_users
```
*Creates test users for all roles with default passwords (change in production!)*

#### 8. Start the Server
```bash
python manage.py runserver
```

**Access the system:**
- **Main Portal:** http://127.0.0.1:8000/
- **Admin Panel:** http://127.0.0.1:8000/admin/
- **API Docs:** http://127.0.0.1:8000/api/

### 📖 Detailed Setup Guide
For complete installation instructions, troubleshooting, and verification steps, see:
**[INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)**

### Initial Configuration
After installation, configure through Django Admin:

1. **Dashboard Settings:** Admin → Workflow → Dashboard Settings
   - Configure refresh intervals, pagination, UI preferences
   
2. **Session Settings:** Admin → Workflow → Session Management Settings
   - Set session timeouts, authentication rules, password policies
   
3. **Production Limits:** Admin → Workflow → Production Limit Settings
   - Configure batch limits, file upload limits, concurrent operations
   
4. **Dashboard Permissions:** Admin → Dashboards → Dashboard Permissions
   - Set role-based access controls for each dashboard type
   
5. **User Management:** Admin → Accounts → Users
   - Create user accounts and assign roles

## 🌟 Future Enhancements

- API Integration capabilities
- Mobile application support
- Advanced analytics dashboard
- Equipment IoT integration
- Automated documentation generation
- Regulatory reporting automation

## 📞 Support

For technical support or bug reports, please contact:
- System Administrator: admin@kpi.com
- Technical Support: support@kpi.com

## 📝 License

Copyright © 2025 Kampala Pharmaceutical Industries
All rights reserved.
