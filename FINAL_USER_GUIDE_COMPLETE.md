# 📚 KAMPALA PHARMACEUTICAL INDUSTRIES
## OPERATIONS SYSTEM - COMPLETE USER GUIDE
### Final Training Manual - December 2025

---

## 📋 TABLE OF CONTENTS

1. [System Overview & Introduction](#1-system-overview--introduction)
2. [Getting Started - First Time Login](#2-getting-started---first-time-login)
3. [Product Management](#3-product-management)
4. [User Management & Roles](#4-user-management--roles)
5. [BMR Creation & Management](#5-bmr-creation--management)
6. [Production Workflow Operations](#6-production-workflow-operations)
7. [Quality Control & Quarantine](#7-quality-control--quarantine)
8. [Reports & Analytics](#8-reports--analytics)
9. [Excel & Word Export Features](#9-excel--word-export-features)
10. [Django Admin Interface - Superuser Guide](#10-django-admin-interface---superuser-guide)
11. [System Configuration & Settings](#11-system-configuration--settings)
12. [Dashboard Permissions Management](#12-dashboard-permissions-management)
13. [Troubleshooting & Support](#13-troubleshooting--support)

---

## 1. SYSTEM OVERVIEW & INTRODUCTION

### 1.1 What is the KPI Operations System?

The Kampala Pharmaceutical Industries Operations System is a comprehensive web-based platform designed to manage the complete pharmaceutical production lifecycle from raw materials to finished goods storage.

**Key Features:**
- ✅ Complete BMR (Batch Manufacturing Record) lifecycle management
- ✅ Real-time production workflow tracking
- ✅ Quality control integration with quarantine management
- ✅ Electronic signatures and complete audit trails
- ✅ Machine and equipment monitoring
- ✅ Advanced analytics and reporting
- ✅ Role-based access control (24 different user roles)
- ✅ Export capabilities (Excel, Word, CSV)

### 1.2 Supported Product Types

The system manages four main product categories:

#### **Ointments**
- **Workflow**: Material Dispensing → Mixing → Tube Filling → Packaging → Finished Goods
- **Use Case**: Topical creams and ointments
- **Key Phases**: Mixing, Tube Filling

#### **Tablets (Normal)**
- **Workflow**: Material Dispensing → Granulation → Blending → Compression → [Optional: Coating] → Blister Packing → Finished Goods
- **Use Case**: Standard oral solid dosage forms
- **Key Phases**: Granulation, Compression, Blister Packing

#### **Tablets (Type 2)**
- **Workflow**: Material Dispensing → Granulation → Blending → Compression → [Optional: Coating] → Bulk Packing → Finished Goods
- **Use Case**: Tablets for bulk distribution
- **Key Phases**: Same as normal tablets but with bulk packaging

#### **Capsules**
- **Workflow**: Material Dispensing → Drying → Blending → Filling → Blister Packing → Finished Goods
- **Use Case**: Powder/granule-filled capsules
- **Key Phases**: Drying, Capsule Filling

### 1.3 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB BROWSER ACCESS                           │
│              http://192.168.1.244:8000                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    USER AUTHENTICATION                          │
│         (Role-based access, Session management)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ROLE-SPECIFIC DASHBOARDS                     │
│  Admin | QA | Production | QC | Operators | Store Manager     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CORE SYSTEM MODULES                          │
│  BMR Management | Workflow Engine | Quality Control            │
│  Inventory | Analytics | Reports | Notifications               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE & FILE STORAGE                      │
│         SQLite Database | Audit Logs | Documents               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 System Requirements

**For Users (Client Side):**
- Modern web browser (Chrome 90+, Firefox 88+, Edge 90+)
- Internet/Network connection to server
- Screen resolution: Minimum 1024x768, Recommended 1920x1080
- No special software installation required

**Server Specifications:**
- Server IP: 192.168.1.244
- Port: 8000
- Operating System: Windows Server
- Web Server: Waitress WSGI Server
- Database: SQLite
- Python: 3.12.10
- Django: 4.2.7

### 1.5 Key System Concepts

#### **BMR (Batch Manufacturing Record)**
A BMR is the complete documentation of a manufacturing batch from start to finish. It includes:
- Product specifications
- Batch number (format: XXXYYYY, e.g., 0012025)
- Material requirements
- Manufacturing instructions
- Quality control checkpoints
- Electronic signatures
- Complete audit trail

#### **Production Phases**
Production is divided into sequential phases, each handled by specific operators:
- Material Dispensing
- Mixing/Granulation/Drying (depending on product type)
- Blending
- Compression/Filling/Tube Filling
- Coating (optional)
- Packing (Blister/Bulk)
- Quality Control checkpoints
- Finished Goods Storage

#### **Quality Gates**
The system enforces quality checkpoints at critical phases:
- **Post-Mixing QC**: After mixing/blending
- **Post-Granulation QC**: After granulation (tablets)
- **Post-Compression QC**: After compression (tablets)
- **Quality Control**: Before packing
- **Final QA**: Before finished goods release

#### **Quarantine System**
Failed quality checks trigger automatic quarantine:
- Batch is held in quarantine
- Up to 2 samples can be requested
- QA performs sampling
- QC performs testing
- Batch either released or sent back for rework

---

**[Screenshot Placeholder: System Dashboard Overview]**
*Caption: Main system dashboard showing navigation and key metrics*

---

## 2. GETTING STARTED - FIRST TIME LOGIN

### 2.1 Accessing the System

**System URL:** `http://192.168.1.244:8000`

**Login Page URL:** `http://192.168.1.244:8000/accounts/login/`

**Admin Panel URL:** `http://192.168.1.244:8000/admin/`

### 2.2 User Credentials

All users have been pre-created with default passwords. Contact your system administrator for your username and password.

**Default Password Pattern:** `[role]123`

Examples:
- QA User: `qa123`
- Mixing Operator: `mixing123`
- Store Manager: `store123`
- Admin: `admin123`

### 2.3 Step-by-Step First Login

**Step 1: Open Your Web Browser**
- Launch Chrome, Firefox, or Edge
- Type the system URL: `http://192.168.1.244:8000`
- Press Enter

**Step 2: Navigate to Login Page**
- You'll be automatically redirected to the login page
- Or click "Login" if you see the home page

**Step 3: Enter Your Credentials**
```
Username: [Your assigned username]
Password: [Your assigned password]
```

**Step 4: Click "Login" Button**
- System validates your credentials
- You'll see a loading indicator briefly

**Step 5: Automatic Dashboard Redirect**
- System automatically redirects you to your role-specific dashboard
- Each role sees different dashboard features

### 2.4 Understanding Your Dashboard

After login, you'll see your personalized dashboard based on your role:

#### **Admin Dashboard Features:**
- System overview statistics
- All BMRs tracking
- Production timeline
- Monthly analytics
- System health monitoring
- User management access
- Export tools

#### **QA Dashboard Features:**
- BMR creation form
- Pending BMR requests from production
- BMRs awaiting final approval
- Quality review queue
- My created BMRs

#### **Production Manager Dashboard Features:**
- Request new BMR form
- My BMR requests status
- Active production batches
- Production planning tools

#### **Operator Dashboard Features:**
- My assigned phases
- Phases ready to start
- Phases in progress
- Phase completion forms
- Machine selection

#### **QC Dashboard Features:**
- Testing queue
- Pending samples
- Test result entry forms
- Approval/rejection actions

#### **Store Manager Dashboard Features:**
- Material release requests
- Inventory status
- Pending dispensing tasks

### 2.5 Navigation Menu

**Top Navigation Bar:**
- **Company Logo**: Click to return to dashboard
- **User Name**: Shows your logged-in name
- **Logout Button**: End your session

**Sidebar Navigation (Admin/QA/Manager roles):**
- **Overview**: Dashboard home
- **Production Management**: Machine, quality, inventory
- **Quarantine Tracking**: Quarantine management
- **Notifications & Alerts**: System notifications
- **System Administration**: User management, settings (Admin/Superuser only)

### 2.6 Session Management

**Session Timeout:**
- Default: 30 minutes of inactivity
- System will automatically log you out
- You'll see a timeout warning before logout
- Save your work frequently

**Security Best Practices:**
- Always logout when finished
- Don't share your credentials
- Don't leave your computer unattended while logged in
- Report suspicious activity immediately

### 2.7 Changing Your Password (First Time Recommended)

**For Regular Users:**
1. Contact system administrator to change password
2. Admin can reset via Django Admin panel

**For Admin Users:**
1. Go to: `http://192.168.1.244:8000/admin/`
2. Click on "Users" under "ACCOUNTS"
3. Find your user account
4. Click "Change password" link
5. Enter new password twice
6. Click "Save"

### 2.8 Common First Login Issues

**Problem: "Invalid credentials" error**
- **Solution**: Check username spelling (case-sensitive)
- Verify password (check Caps Lock)
- Contact admin if account is locked

**Problem: Login page won't load**
- **Solution**: Check network connection
- Verify server is running
- Try different browser
- Clear browser cache

**Problem: Blank page after login**
- **Solution**: Wait 5-10 seconds for dashboard to load
- Refresh the page
- Check browser console for errors
- Contact IT support

**Problem: "Access Denied" message**
- **Solution**: Your role may not have dashboard access
- Contact administrator to verify role assignment
- May need permission update

---

**[Screenshot Placeholder: Login Page]**
*Caption: System login page with username and password fields*

**[Screenshot Placeholder: QA Dashboard Example]**
*Caption: QA role dashboard showing BMR creation and management features*

**[Screenshot Placeholder: Operator Dashboard Example]**
*Caption: Production operator dashboard showing assigned phases*

---

## 3. PRODUCT MANAGEMENT

### 3.1 Accessing Product Management (Admin/Superuser Only)

Products must be created before any BMRs can be made. This is done through the Django Admin interface.

**Access Path:**
1. Login as Admin/Superuser
2. Navigate to: `http://192.168.1.244:8000/admin/`
3. Look for "PRODUCTS" section
4. Click on "Products"

### 3.2 Creating a New Product

**Step 1: Click "Add Product" Button**
- Located at top right of Products list page
- Green "+ Add Product" button

**Step 2: Fill in Basic Information**

```
Product Name: [Enter full product name]
Example: "Paracetamol 500mg Tablets"

Product Type: [Select from dropdown]
Options:
- ointment
- tablet
- capsule
```

**Step 3: Configure Product Type Specific Fields**

**For Tablets:**
```
Coating Type: [Select one]
- coated
- uncoated

Tablet Type: [Select one]
- normal (uses Blister Packing)
- tablet_2 (uses Bulk Packing)
```

**For All Products:**
```
Standard Batch Size: [Number, e.g., 10000]
Batch Size Unit: [Select from dropdown]
- tablets
- capsules
- tubes
- units

Packaging Size in Units: [Number, e.g., 10]
(How many units per package)
```

**Step 4: Set Active Status**
```
☑ Is Active
(Check this box to make product available for BMR creation)
```

**Step 5: Click "Save" Button**
- Click "Save and add another" to create more products
- Click "Save and continue editing" to add more details
- Click "Save" to return to products list

### 3.3 Product Workflow Templates

The system automatically assigns workflow phases based on product type:

**Ointment Workflow:**
1. Material Dispensing
2. Mixing
3. Post-Mixing QC
4. Tube Filling
5. Quality Control
6. Packaging Material Release
7. Secondary Packing
8. Final QA
9. Finished Goods Store

**Tablet (Normal) Workflow:**
1. Material Dispensing
2. Granulation
3. Post-Granulation QC
4. Blending
5. Post-Blending QC
6. Compression
7. Post-Compression QC
8. Coating (if product.coating_type = "coated")
9. Sorting
10. Quality Control
11. Blister Packing
12. Packaging Material Release
13. Secondary Packing
14. Final QA
15. Finished Goods Store

**Tablet (Type 2) Workflow:**
- Same as Normal Tablet, but step 11 is "Bulk Packing" instead of "Blister Packing"

**Capsule Workflow:**
1. Material Dispensing
2. Drying
3. Blending
4. Post-Blending QC
5. Filling (capsule filling)
6. Quality Control
7. Blister Packing
8. Packaging Material Release
9. Secondary Packing
10. Final QA
11. Finished Goods Store

### 3.4 Viewing Product List

**Access:** Admin Panel → Products → Products

**Information Displayed:**
- Product ID
- Product Name
- Product Type
- Coating Type (tablets)
- Tablet Type (tablets)
- Batch Size
- Active Status
- Created Date

**Actions Available:**
- **View**: Click on product name
- **Edit**: Click on product name, modify fields, save
- **Delete**: Select product, choose "Delete selected products" from actions
- **Duplicate**: View product, save as new with different name

### 3.5 Editing Existing Products

**Warning:** Changing product configuration affects NEW BMRs only. Existing BMRs maintain their original workflow.

**To Edit:**
1. Go to Admin Panel → Products → Products
2. Click on product name to edit
3. Modify fields as needed
4. Click "Save"

**Recommended Changes:**
- ✅ Product name (for clarity)
- ✅ Batch size (if standard changes)
- ✅ Active status (to disable discontinued products)

**Not Recommended to Change:**
- ❌ Product type (creates workflow confusion)
- ❌ Coating/Tablet type on products with existing BMRs

### 3.6 Deactivating Products

Instead of deleting products (which may have historical BMRs), deactivate them:

1. Edit the product
2. Uncheck "☑ Is Active"
3. Save

**Result:** Product won't appear in BMR creation dropdown but historical data remains intact.

### 3.7 Product Ingredients Management (Optional)

**Access:** Admin Panel → Products → Product Ingredients

Add ingredient information for each product:
```
Product: [Select product]
Ingredient Name: [e.g., "Paracetamol API"]
Ingredient Type: [active|inactive|excipient]
Quantity per Unit: [e.g., 500]
Unit of Measure: [mg|g|ml|%]
Supplier: [Supplier name]
```

### 3.8 Product Specifications (Optional)

**Access:** Admin Panel → Products → Product Specifications

Add quality specifications:
```
Product: [Select product]
Parameter Name: [e.g., "Assay"]
Specification: [e.g., "95.0-105.0%"]
Test Method: [e.g., "HPLC"]
Acceptance Criteria: [e.g., "Must be within spec"]
```

---

**[Screenshot Placeholder: Product List in Admin Panel]**
*Caption: Admin panel showing list of configured products*

**[Screenshot Placeholder: Add Product Form]**
*Caption: Product creation form with all fields visible*

**[Screenshot Placeholder: Product Type Dropdown]**
*Caption: Product type selection showing ointment, tablet, capsule options*

---

## 4. USER MANAGEMENT & ROLES

### 4.1 Understanding User Roles (24 Total Roles)

The system supports 24 distinct user roles, each with specific permissions and dashboard access.

#### **Administrative Roles**

**Admin/Superuser**
- Complete system access
- User management
- System configuration
- All dashboard features
- Django Admin panel access

**QA (Quality Assurance)**
- BMR creation and management
- Quality reviews and final approvals
- BMR request management
- Final batch certification

**Regulatory Affairs**
- BMR regulatory approval
- Compliance oversight
- Documentation reviews

#### **Management Roles**

**Production Manager**
- BMR requests to QA
- Production planning
- Resource allocation
- Production oversight

**Store Manager**
- Raw material management
- Inventory control
- Material release authorization

**Dispensing Manager**
- Material dispensing oversight
- Batch preparation management

**QC (Quality Control)**
- Testing and laboratory analysis
- Sample approval/rejection
- Test result recording

**Quarantine Manager**
- Quarantine batch management
- Sample request processing
- Batch isolation control

#### **Storage Roles**

**Packaging Store**
- Packaging material management
- Material releases for packing operations

**Finished Goods Store**
- Final product storage
- Distribution management
- Sales order fulfillment

#### **Production Operators (14 Roles)**

**Mixing Operator**
- Handles mixing operations for ointments
- Post-mixing documentation

**Tube Filling Operator**
- Tube filling for ointments
- Tube fill accuracy monitoring

**Granulation Operator**
- Wet/dry granulation for tablets
- Granule quality monitoring

**Blending Operator**
- Final blending operations
- Blend uniformity verification

**Compression Operator**
- Tablet compression operations
- Weight and hardness monitoring

**Coating Operator**
- Tablet coating operations (optional phase)
- Coating quality verification

**Drying Operator**
- Material drying for capsules
- Moisture content monitoring

**Filling Operator**
- Capsule filling operations
- Fill weight accuracy

**Sorting Operator**
- Product sorting and visual inspection
- Defect identification

**Packing Operator**
- Handles all packing types:
  - Blister packing (tablets, capsules)
  - Bulk packing (Type 2 tablets)
  - Secondary packaging

**Dispensing Operator**
- Material dispensing operations
- Dispensing documentation

**Equipment Operator**
- Equipment operations and setup
- Basic maintenance tasks

**Cleaning Operator**
- Line clearance
- Equipment cleaning
- Sanitation verification

### 4.2 Creating New Users (Admin/Superuser Only)

**Access Path:**
1. Login as Admin/Superuser
2. Navigate to: `http://192.168.1.244:8000/admin/`
3. Under "ACCOUNTS" section, click "Users"
4. Click "+ Add User" button (top right)

**Step 1: Basic User Information**
```
Username: [Unique username, lowercase recommended]
Password: [Enter twice for confirmation]
```
Click "Save and continue editing"

**Step 2: Personal Information**
```
First Name: [User's first name]
Last Name: [User's last name]
Email: [user@kampalapharma.com]
```

**Step 3: Role Assignment**
```
Role: [Select from dropdown - very important!]
Options:
- admin
- qa
- regulatory
- production_manager
- store_manager
- dispensing_manager
- qc
- quarantine
- packaging_store
- finished_goods_store
- mixing_operator
- tube_filling_operator
- granulation_operator
- blending_operator
- compression_operator
- coating_operator
- drying_operator
- filling_operator
- sorting_operator
- packing_operator
- dispensing_operator
- equipment_operator
- cleaning_operator
```

**Step 4: Permissions (Usually not needed)**
```
☑ Active: Check to enable account
☐ Staff status: Check only for admin access to Django Admin
☐ Superuser status: Check only for full system access
```

**Step 5: Click "Save"**

### 4.3 Viewing All Users

**Access:** Admin Panel → Accounts → Users

**Information Displayed:**
- Username
- Email
- First Name
- Last Name
- Role
- Staff Status
- Active Status

**Search/Filter Options:**
- Search by username, email, or name
- Filter by role
- Filter by staff status
- Filter by active status

### 4.4 Editing User Information

**To Edit User:**
1. Admin Panel → Accounts → Users
2. Click on username to edit
3. Modify fields as needed
4. Click "Save"

**Common Edits:**
- Change role assignment
- Update contact information
- Activate/deactivate account
- Reset password

### 4.5 Resetting User Passwords

**Method 1: Django Admin (Recommended)**
1. Admin Panel → Accounts → Users
2. Click on user to edit
3. Click "this form" link next to password field
4. Enter new password twice
5. Click "Change password"

**Method 2: Bulk Password Reset**
1. Admin Panel → Accounts → Users
2. Select multiple users (checkboxes)
3. Choose "Reset passwords to default (role123)" from Actions dropdown
4. Click "Go"

**Result:** Passwords reset to pattern: `[role]123`
- QA user → `qa123`
- Mixing operator → `mixing123`
- Store manager → `store123`

### 4.6 Deactivating Users

Instead of deleting users (which loses audit trail), deactivate them:

1. Edit the user
2. Uncheck "☑ Active"
3. Save

**Result:** User cannot login but historical data (BMR creation, phase execution) remains intact.

### 4.7 User Session Management

**Viewing Active Sessions:**
- Admin Panel → Accounts → User Sessions
- Shows all active user sessions
- Displays login time and IP address

**Ending User Sessions:**
- Select sessions
- Choose "Delete selected sessions" action
- Click "Go"

**Session Timeout Settings:**
- Default: 30 minutes of inactivity
- Configurable in: Workflow → Session Management Settings
- Field: `session_timeout_minutes`

### 4.8 Default User Credentials Reference

All system users are pre-created with default passwords:

**Administrative Access:**
```
admin / admin123 (Superuser)
qa_user / qa123 (QA)
regulatory_user / regulatory123
```

**Management:**
```
production_manager / production123
store_manager / store123
qc_user / qc123
```

**Production Operators:**
```
mixing_operator / mixing123
granulation_operator / granulation123
blending_operator / blending123
compression_operator / compression123
coating_operator / coating123
drying_operator / drying123
filling_operator / filling123
tube_filling_operator / tube123
sorting_operator / sorting123
packing_operator / packing123
dispensing_operator / dispensing123
equipment_operator / equipment123
cleaning_operator / cleaning123
```

**⚠️ Security Reminder:** Change all default passwords in production environment!

---

**[Screenshot Placeholder: User List in Admin Panel]**
*Caption: List of all system users with roles and status*

**[Screenshot Placeholder: Add User Form]**
*Caption: User creation form showing role dropdown selection*

**[Screenshot Placeholder: Role Assignment Dropdown]**
*Caption: Complete list of 24 available user roles*

---

## 5. BMR CREATION & MANAGEMENT

### 5.1 BMR Workflow Overview

The complete BMR lifecycle follows this flow:

```
Production Manager → Request BMR
         ↓
QA → Create BMR (Manual batch number entry)
         ↓
Regulatory → Approve BMR
         ↓
Production Phases → Execute workflow
         ↓
QC → Quality testing checkpoints
         ↓
Final QA → Approve completed batch
         ↓
Finished Goods Store → Storage
```

### 5.2 Requesting a BMR (Production Manager Role)

**Step 1: Access BMR Request Form**
- Login as Production Manager
- Dashboard shows "Request New BMR" button
- Or navigate to BMR Requests section
- Click "Create BMR Request"

**Step 2: Fill Request Form**
```
Product: [Select from dropdown of active products]
Requested Quantity: [Number of units]
Planned Start Date: [Select date from calendar]
Urgency Level: [normal | urgent | critical]
Justification: [Business reason for production]
Special Instructions: [Any special notes]
```

**Step 3: Submit Request**
- Click "Submit Request" button
- Request appears in QA dashboard
- You'll receive notification when QA creates BMR

**Step 4: Track Request Status**
- View "My BMR Requests" table
- Status options:
  - **Pending**: Waiting for QA action
  - **Approved**: QA created BMR
  - **Rejected**: QA rejected request with reason

### 5.3 Creating a BMR (QA Role)

**Step 1: Access Pending Requests**
- Login as QA user
- Dashboard shows "BMR Requests from Production" section
- Review pending requests

**Step 2: Click "Create BMR" Button**
- Click on desired request
- System opens BMR creation form
- Some fields pre-filled from request

**Step 3: Fill BMR Information**

**Basic Information:**
```
Product: [Pre-selected from request]
Batch Number: [MUST ENTER MANUALLY - Format: XXXYYYY]
Example: 0012025 (1st batch of 2025)
         0152024 (150th batch of 2024)

Manufacturing Date: [Select date]
```

**Batch Specifications:**
```
Actual Batch Size: [Number of units to produce]
Actual Batch Size Unit: [tablets | capsules | tubes | units]
Packaging Size in Units: [Auto-filled from product]
```

**Planning Dates:**
```
Planned Start Date: [When production should start]
Planned Completion Date: [Expected completion date]
```

**Manufacturing Instructions:**
```
Manufacturing Instructions: [Detailed step-by-step procedures]
Special Instructions: [Any special handling requirements]
In Process Controls: [Quality checkpoints during production]
Quality Checks Required: [Testing requirements]
```

**QA Comments:**
```
QA Comments: [Your notes and observations]
```

**Step 4: Add Material Requirements**

Click "Add Material" section:
```
Material Name: [e.g., "Paracetamol API"]
Required Quantity: [Amount needed]
Unit of Measure: [kg | L | units | g | mg]
Specification: [Quality specification]
Supplier: [Approved supplier name]
Lot Number: [If known, otherwise filled during dispensing]
Expiry Date: [Material expiry]
```

Click "+ Add Another Material" to add more materials.

**Step 5: Review and Save**
- Review all entered information
- Click "Save as Draft" to save without submitting
- Click "Submit for Approval" to send to Regulatory

**Step 6: BMR Status After Creation**
- **Draft**: Saved but not submitted
- **Submitted**: Sent to Regulatory for approval
- **Approved**: Regulatory approved, ready for production
- **Rejected**: Regulatory rejected, needs revision

### 5.4 BMR Approval (Regulatory Role)

**Step 1: Access Pending BMRs**
- Login as Regulatory user
- Dashboard shows "BMRs Pending Regulatory Approval"
- List shows all submitted BMRs

**Step 2: Review BMR Details**
- Click "View BMR" button
- Review all information:
  - Product specifications
  - Batch number (verify format: XXXYYYY)
  - Manufacturing instructions
  - Material requirements
  - Quality checkpoints

**Step 3: Make Decision**

**To Approve:**
```
1. Click "Approve BMR" button
2. Enter regulatory comments (optional)
3. Click "Confirm Approval"
4. System changes status to "Approved"
5. BMR enters production workflow
```

**To Reject:**
```
1. Click "Reject BMR" button
2. Enter reason for rejection (required)
3. Click "Confirm Rejection"
4. BMR returns to QA for revision
5. QA receives notification
```

### 5.5 Batch Number Validation Rules

**Format Requirements:**
- Must be exactly 7 characters
- Format: XXXYYYY
- First 3 digits: Batch sequence (001, 002, 003...)
- Last 4 digits: Year (2025, 2026...)

**Valid Examples:**
- `0012025` ✅ (1st batch of 2025)
- `0022025` ✅ (2nd batch of 2025)
- `1502024` ✅ (150th batch of 2024)

**Invalid Examples:**
- `12025` ❌ (too short)
- `00012025` ❌ (too long)
- `ABC2025` ❌ (contains letters)
- `0012025` ❌ (if already exists - must be unique)

**System Validation:**
- System checks batch number uniqueness
- Error message if duplicate found
- Error message if format incorrect
- Cannot proceed until valid unique batch number entered

### 5.6 Viewing BMR List

**Access:**
- Click "BMR List" in navigation
- Or from dashboard "View All BMRs" link

**Information Displayed:**
- BMR Number (auto-generated system ID)
- Batch Number (your manual entry)
- Product Name and Type
- Status
- Created Date
- Created By
- Actions (View, Edit, Delete)

**Filtering BMRs:**
- **By Status**: Click status filter buttons
  - All BMRs
  - Draft
  - Approved
  - In Production
  - Completed
  - Rejected

**Status Filter from Dashboard Cards:**
- Click dashboard overview cards
- System automatically filters BMR list
- Example: Click "Active Batches" → Shows draft, approved, in_production BMRs

**Searching BMRs:**
- Use search box to find by:
  - Batch number
  - Product name
  - BMR number

### 5.7 Viewing BMR Details

**Access:**
- From BMR list, click on batch number or "View" button
- Detailed view shows:

**BMR Information Tab:**
- Complete BMR details
- Product specifications
- Batch information
- Dates and planning
- Manufacturing instructions
- Material requirements
- Electronic signatures

**Production Phases Tab:**
- All workflow phases
- Phase status
- Started/Completed dates
- Duration
- Operators assigned
- Machine used
- Comments

**Quality Control Tab:**
- QC checkpoints
- Test results
- Approvals/rejections
- Quarantine history

**Timeline Tab:**
- Visual timeline of production
- Phase progress bars
- Bottleneck identification
- Duration analysis

### 5.8 Editing BMRs

**Draft BMRs (QA Only):**
- Can edit all fields
- Change product (will regenerate workflow)
- Modify batch size
- Update instructions
- Edit materials

**Approved BMRs:**
- **Cannot edit** most fields (regulatory requirement)
- Can add comments only
- Changes require creating new BMR

**Important:** Once approved, BMR is locked for GMP compliance.

### 5.9 Electronic Signatures

BMRs require electronic signatures at key stages:

**BMR Creation Signature:**
- QA user automatically signs upon creation
- Captured: Username, date/time, action

**Regulatory Approval Signature:**
- Regulatory user signs upon approval
- Captured: Username, date/time, approval decision

**Production Completion Signature:**
- QA signs upon final approval
- Captured: Username, date/time, release decision

**Viewing Signatures:**
- BMR Detail page → "Signatures" tab
- Shows all electronic signatures with timestamps

---

**[Screenshot Placeholder: BMR Request Form (Production Manager)]**
*Caption: Production manager BMR request form*

**[Screenshot Placeholder: BMR Creation Form (QA)]**
*Caption: QA BMR creation form with manual batch number entry*

**[Screenshot Placeholder: Batch Number Format Validation]**
*Caption: System validation for batch number format XXXYYYY*

**[Screenshot Placeholder: BMR List with Filters]**
*Caption: BMR list showing status filters and search*

**[Screenshot Placeholder: BMR Detail View]**
*Caption: Complete BMR details showing all tabs*

---

## 6. PRODUCTION WORKFLOW OPERATIONS

### 6.1 Understanding Production Phases

Production is divided into sequential phases. Each phase:
- Must be completed before next phase starts
- Requires specific operator role
- May require machine selection
- Includes start/completion timestamps
- Captures operator comments
- Tracks quality checkpoints

### 6.2 Phase Assignment and Visibility

**How Operators See Their Phases:**
- Login to operator dashboard
- Dashboard shows "My Assigned Phases"
- Only phases matching your role appear
- Phases organized by status:
  - **Ready to Start**: Previous phase completed
  - **In Progress**: You've started but not completed
  - **Completed**: Finished phases

### 6.3 Starting a Production Phase (All Operators)

**Step 1: Identify Ready Phase**
- Dashboard shows phases with "Ready to Start" status
- Phase card shows:
  - BMR/Batch number
  - Product name
  - Phase name
  - Expected duration

**Step 2: Review Phase Requirements**
- Click "View Details" to see:
  - Manufacturing instructions
  - Special requirements
  - Previous phase notes
  - Machine requirements (if applicable)

**Step 3: Select Machine (If Required)**

Phases requiring machine selection:
- Granulation
- Blending
- Compression
- Coating
- Blister Packing
- Bulk Packing
- Filling (capsules)

```
Machine Selection Dropdown:
[Select machine from available machines]
Example: "Granulation Machine - GM001"
```

**Step 4: Click "Start Phase" Button**
- Enter start comments (optional but recommended)
- Click "Confirm Start"
- System records:
  - Start timestamp
  - Operator username
  - Machine selected (if applicable)
  - Start comments

**Step 5: Phase Status Changes**
- Status changes from "Pending" to "In Progress"
- Phase timer starts automatically
- Phase appears in "In Progress" section of your dashboard

### 6.4 During Phase Execution

**Monitor Phase Timer:**
- Real-time countdown/count-up display
- Shows elapsed time
- Color indicators:
  - 🟢 Green: Normal operation
  - 🟡 Yellow: Approaching expected duration
  - 🔴 Red: Exceeding expected duration

**Recording Process Data:**
- Follow manufacturing instructions
- Note any deviations
- Monitor equipment parameters
- Record observations

**Handling Equipment Issues:**

**If Breakdown Occurs:**
```
1. Note the time breakdown started
2. Follow your SOP for breakdown handling
3. When completing phase, you'll record:
   - Breakdown occurred: Yes
   - Breakdown start time
   - Breakdown end time
   - Breakdown reason
   - System calculates duration automatically
```

**If Changeover Needed:**
```
1. Note changeover start time
2. Perform changeover per SOP
3. When completing phase, record:
   - Changeover occurred: Yes
   - Changeover start time
   - Changeover end time
   - Changeover reason
   - System calculates duration
```

### 6.5 Completing a Production Phase

**Step 1: Ensure All Work Complete**
- All manufacturing steps finished
- Equipment cleaned (if required)
- Quality checks performed
- Documentation complete

**Step 2: Click "Complete Phase" Button**
- Located on phase card or detail page

**Step 3: Fill Completion Form**

**Required Information:**
```
Completion Comments: [Your observations and notes]

Was there a breakdown?
○ Yes  ○ No

[If Yes:]
  Breakdown Start Time: [Select time]
  Breakdown End Time: [Select time]
  Breakdown Reason: [Describe issue]
  Duration: [Auto-calculated]

Was there a changeover?
○ Yes  ○ No

[If Yes:]
  Changeover Start Time: [Select time]
  Changeover End Time: [Select time]
  Changeover Reason: [Describe changeover]
  Duration: [Auto-calculated]
```

**Step 4: Click "Confirm Completion"**
- System records:
  - Completion timestamp
  - Total phase duration
  - Breakdown time (if any)
  - Changeover time (if any)
  - Operator comments

**Step 5: Automatic Next Phase Trigger**
- System checks if next phase requires QC
- If QC required: Batch goes to quarantine
- If no QC: Next phase becomes "Ready to Start"
- Next operator sees phase in their dashboard

### 6.6 Role-Specific Phase Operations

#### **Material Dispensing (Dispensing Operator)**

**Process:**
1. Receive BMR with material list
2. Collect required materials from store
3. Weigh/measure each material
4. Record actual quantities dispensed
5. Label containers with:
   - Batch number
   - Material name
   - Quantity
   - Date
   - Your signature

**Documentation:**
- Material name
- Required quantity
- Actually dispensed quantity
- Lot numbers
- Expiry dates

#### **Mixing Operations (Mixing Operator - Ointments)**

**Process:**
1. Start mixing phase
2. Select mixing equipment
3. Load materials per BMR
4. Mix for specified duration
5. Monitor temperature/RPM
6. Take in-process samples
7. Complete phase with observations

**Machine Required:** Yes - Select mixer

#### **Granulation (Granulation Operator - Tablets)**

**Process:**
1. Start granulation phase
2. Select granulation machine
3. Load powder blend
4. Add binder solution as specified
5. Granulate per BMR parameters
6. Dry granules if required
7. Complete with granule characteristics

**Machine Required:** Yes - Select granulator

#### **Blending (Blending Operator - Tablets & Capsules)**

**Process:**
1. Start blending phase
2. Select blender
3. Load granules/powders
4. Blend for specified time
5. Check blend uniformity
6. Complete with blend observations

**Machine Required:** Yes - Select blender

#### **Compression (Compression Operator - Tablets)**

**Process:**
1. Start compression phase
2. Select compression machine
3. Set up tooling
4. Adjust parameters (weight, hardness, thickness)
5. Run production
6. Monitor weight uniformity
7. Record in-process checks
8. Complete with compression data

**Machine Required:** Yes - Select tablet press

**Key Monitoring:**
- Average tablet weight
- Weight variation
- Hardness
- Thickness
- Friability

#### **Coating (Coating Operator - Coated Tablets)**

**Note:** This phase only appears for products configured as "coated"

**Process:**
1. Start coating phase
2. Select coating machine
3. Load compressed tablets
4. Prepare coating solution
5. Apply coating per parameters
6. Monitor coat weight gain
7. Dry coated tablets
8. Complete with coating quality notes

**Machine Required:** Yes - Select coater

#### **Filling Operations (Filling Operator - Capsules)**

**Process:**
1. Start filling phase
2. Select capsule filling machine
3. Set up capsule size
4. Adjust fill weight
5. Run production
6. Monitor fill weight uniformity
7. Complete with filling data

**Machine Required:** Yes - Select capsule filler

#### **Tube Filling (Tube Filling Operator - Ointments)**

**Process:**
1. Start tube filling phase
2. Select tube filling machine
3. Set up tube size
4. Adjust fill weight/volume
5. Fill tubes
6. Seal tubes
7. Complete with fill accuracy data

**Machine Required:** Yes - Select tube filler

#### **Packing Operations (Packing Operator - All Products)**

**Handles Three Packing Types:**

**Blister Packing (Normal Tablets & Capsules):**
```
1. Start blister packing phase
2. Select blister machine
3. Load product and blister material
4. Set up pack size (e.g., 10 tablets/blister)
5. Run packing
6. Monitor pack quality
7. Count and record output
8. Complete with packing data
```

**Bulk Packing (Type 2 Tablets):**
```
1. Start bulk packing phase
2. Select bulk packing equipment
3. Weigh and fill bulk containers
4. Label containers per requirements
5. Record container numbers and weights
6. Complete with packing summary
```

**Secondary Packing (All Products):**
```
1. Start secondary packing phase
2. Pack blisters/tubes into cartons
3. Add package inserts
4. Label cartons
5. Record carton numbers
6. Complete with final pack count
```

**Machine Required:** Yes (for blister/bulk) - Select packing machine

### 6.7 Quality Checkpoints During Production

**Automatic QC Phases:**

**Post-Mixing QC** (Ointments)
- After mixing phase
- Before tube filling
- QC operator tests blend

**Post-Granulation QC** (Tablets)
- After granulation
- Before blending
- QC tests granule properties

**Post-Blending QC** (Tablets & Capsules)
- After blending
- Before compression/filling
- QC tests blend uniformity

**Post-Compression QC** (Tablets)
- After compression
- Before coating/sorting
- QC tests tablet quality

**Quality Control** (All Products)
- After packing
- Before final QA
- Comprehensive product testing

### 6.8 Viewing Production History

**For Operators:**
- Dashboard shows "My History" section
- Lists all phases you've executed
- Shows completion dates and durations

**For Managers/Admin:**
- Admin dashboard "BMR Timeline Tracking"
- Shows all phases across all batches
- Color-coded status indicators
- Export to Excel/CSV available

### 6.9 Handling Phase Errors

**If You Started Wrong Phase:**
1. Contact supervisor immediately
2. Do NOT complete the phase
3. Admin can reset phase status
4. Proper phase can then be started

**If Equipment Fails Mid-Phase:**
1. Record breakdown information
2. Complete phase when equipment fixed
3. Enter detailed breakdown comments
4. System tracks downtime separately

**If Quality Issue Discovered:**
1. Stop the phase immediately
2. Contact QC/QA
3. Do NOT complete phase
4. May need to quarantine batch
5. Investigation required before proceeding

---

**[Screenshot Placeholder: Operator Dashboard - Assigned Phases]**
*Caption: Operator dashboard showing ready-to-start and in-progress phases*

**[Screenshot Placeholder: Start Phase Form with Machine Selection]**
*Caption: Phase start form showing machine selection dropdown*

**[Screenshot Placeholder: Phase Timer Display]**
*Caption: Real-time phase timer with color status indicators*

**[Screenshot Placeholder: Complete Phase Form]**
*Caption: Phase completion form with breakdown and changeover fields*

**[Screenshot Placeholder: Production Timeline View]**
*Caption: Visual timeline showing all phases for a BMR*

---

## 7. QUALITY CONTROL & QUARANTINE

### 7.1 Quarantine System Overview

When a production phase completes and requires QC approval, the batch automatically enters quarantine until testing is complete.

**Quarantine Flow:**
```
Production Phase Complete
         ↓
Automatic Quarantine
         ↓
Quarantine Manager → Request Sample (max 2)
         ↓
QA → Take Sample
         ↓
QC → Test Sample
         ↓
QC → Approve or Reject
         ↓
If Approved: Release to next phase
If Rejected: Return to previous phase for rework
```

### 7.2 Quarantine Management (Quarantine Manager Role)

**Step 1: View Quarantined Batches**
- Login as Quarantine Manager
- Dashboard shows "Batches in Quarantine"
- Table displays:
  - Batch number
  - Product
  - Current phase
  - Quarantine date
  - Sample status
  - Actions

**Step 2: Request Sample**
- Click "Request Sample" button on quarantined batch
- System limits to maximum 2 samples per batch
- Sample request sent to QA

**Sample Request Information:**
```
Sample Number: [Auto-assigned: 1 or 2]
Requested By: [Your username - automatic]
Request Date: [Current timestamp - automatic]
Status: "Sample Requested"
```

**Step 3: Track Sample Status**
- **Sample Requested**: QA needs to take sample
- **Sample in QA**: QA has taken sample, sent to QC
- **Sample in QC**: QC testing in progress
- **Sample Approved**: QC approved, can release batch
- **Sample Failed**: QC rejected, batch needs rework

**Step 4: Release Batch (After Approval)**
- Once sample approved, "Release Batch" button appears
- Click to release from quarantine
- Batch proceeds to next production phase
- Quarantine record maintained for audit

### 7.3 QA Sampling Process (QA Role)

**Step 1: View Sample Requests**
- Login as QA
- Dashboard shows "Sample Requests Pending"
- Lists all batches needing sampling

**Step 2: Perform Sampling**
- Click "Take Sample" button
- Enter sampling information:

```
Sample Date: [Current date/time - automatic]
Sample Location: [Where sample taken from]
Sample Quantity: [Amount taken]
Sampling Method: [How sample obtained]
QA Comments: [Your observations]
```

**Step 3: Send to QC**
- Click "Send to QC" button
- Sample status changes to "Sample in QC"
- QC receives notification
- Physical sample delivered to QC lab

### 7.4 QC Testing Process (QC Role)

**Step 1: View Testing Queue**
- Login as QC
- Dashboard shows "Samples for Testing"
- Prioritize by:
  - Urgency
  - Quarantine duration
  - Product type

**Step 2: Receive Sample**
- Click "Receive Sample" button
- Enter receipt information:

```
Received Date: [Current date/time]
Received By: [Your name - automatic]
Sample Condition: [Condition of received sample]
QC Comments: [Initial observations]
```

**Step 3: Perform Testing**
- Conduct required QC tests per product specifications
- Record test results
- Follow product-specific test methods

**Step 4: Enter Test Results**
- Click "Enter Results" button
- Complete test results form:

```
Test Results (JSON format or structured fields):
Example:
{
  "Assay": "98.5%",
  "Dissolution": "Pass",
  "Weight Uniformity": "Pass",
  "Hardness": "8.5 kP"
}

Overall Result:
○ Pass  ○ Fail

QC Comments: [Detailed findings and observations]
```

**Step 5: Make Decision**

**To Approve Sample:**
```
1. Select "Pass" result
2. Enter QC comments with justification
3. Click "Approve Sample"
4. Sample status → "Sample Approved"
5. Batch eligible for release from quarantine
```

**To Reject Sample:**
```
1. Select "Fail" result
2. Enter detailed failure reason (required)
3. Specify which tests failed
4. Click "Reject Sample"
5. Sample status → "Sample Failed"
6. Batch returns to previous phase
7. Investigation initiated
```

### 7.5 Quarantine Dashboard Features

**For All Roles (View Access):**
- Current quarantined batches
- Sample status tracking
- Quarantine duration
- Historical quarantine data

**Quarantine Statistics:**
- Total batches in quarantine
- Average quarantine duration
- Sample approval rate
- Pending samples count

### 7.6 Quality Rollback Process

When QC rejects a sample:

**Step 1: Automatic Rollback**
- System automatically changes batch phase status
- Batch returns to phase before QC checkpoint
- Example: If Post-Compression QC fails → Returns to Compression phase

**Step 2: Investigation Required**
- QA/QC must investigate root cause
- Document findings
- Implement corrective actions

**Step 3: Rework Execution**
- Compression operator (continuing example) re-executes phase
- Follows corrective action plan
- Completes phase with detailed comments

**Step 4: Re-testing**
- Batch enters quarantine again
- New sample requested
- QC re-tests
- If pass: Proceeds
- If fail again: May require batch rejection

### 7.7 Maximum Samples Rule

**System Limit:** Maximum 2 samples per quarantine period

**If Both Samples Fail:**
- Batch must be formally rejected OR
- Requires management review and deviation approval
- Cannot request additional samples without proper justification

**Purpose:** Prevents endless testing cycles, ensures process control

### 7.8 Quarantine Reports

**Access:** Reports → Quarantine Reports

**Available Reports:**
- Batches currently in quarantine
- Quarantine history
- Average quarantine duration by product
- Sample failure analysis
- QC performance metrics

**Export Options:**
- Excel
- CSV
- PDF

---

**[Screenshot Placeholder: Quarantine Dashboard]**
*Caption: Quarantine manager dashboard showing quarantined batches*

**[Screenshot Placeholder: Sample Request Form]**
*Caption: Form for requesting QC samples from quarantine*

**[Screenshot Placeholder: QC Test Results Entry]**
*Caption: QC test results entry form with pass/fail options*

**[Screenshot Placeholder: Quarantine Timeline]**
*Caption: Visual timeline of quarantine process from request to release*

---

## 8. REPORTS & ANALYTICS

### 8.1 Available Reports

The system provides comprehensive reporting across all operations:

#### **Production Reports**
- Monthly production analytics
- BMR timeline tracking
- Work in progress (WIP) report
- Completed batches report
- Production efficiency analysis

#### **Quality Reports**
- QC test results
- Quarantine analysis
- Sample failure reports
- Quality trend analysis

#### **Comments & Observations**
- BMR comments report
- Phase execution comments
- QA/QC observations

#### **Timeline Reports**
- Production timeline overview
- Phase duration analysis
- Bottleneck identification
- Resource utilization

### 8.2 Accessing Reports

**For Admin/Manager Roles:**
- Dashboard → Reports section
- Or navigate to Reports menu
- Select report category
- Choose specific report

**For Operators:**
- Limited to "My History" reports
- Personal phase execution history
- Individual performance metrics

### 8.3 Monthly Production Analytics

**Access:** Admin Dashboard → Production Analytics

**Step 1: Select Time Period**
```
Month: [Select from dropdown 1-12]
Year: [Select from dropdown]
Product Type Filter: [All | Ointment | Tablet | Capsule]
```

**Step 2: Click "View Analytics"**

**Dashboard Shows:**
- Total batches completed
- Total units produced
- Production by product type
- Daily production chart
- Weekly production trends
- Top performing products

**Key Metrics Displayed:**
- Batches Completed This Month
- Total Units Produced
- Average Batch Size
- Production Efficiency %
- Quality Pass Rate
- Average Cycle Time

**Charts Available:**
- Daily production bar chart
- Product type distribution pie chart
- Weekly trend line graph
- Product performance comparison

### 8.4 BMR Timeline Tracking

**Access:** Admin Dashboard → BMR Timeline Tracking

**Features:**
- Visual timeline for all BMRs
- Color-coded phase status:
  - 🟢 Green: Completed
  - 🟡 Yellow: In Progress
  - 🔴 Red: Overdue
  - ⚪ Gray: Not Started
  - 🔵 Blue: In Quarantine

**Timeline Information:**
- Batch number
- Product name
- Current phase
- Progress percentage
- Start date
- Expected completion
- Actual status
- Bottleneck phases

**Interactive Features:**
- Click on batch to view details
- Hover for quick info
- Filter by status
- Sort by various criteria

### 8.5 Work in Progress (WIP) Report

**Access:** Admin Dashboard → Work in Progress

**Shows All Active BMRs:**
- BMRs in Draft status
- BMRs Approved but not started
- BMRs In Production

**Information Displayed:**
- Product name
- Batch number
- Batch size
- Current status
- Current phase
- Started date
- Progress percentage
- Expected completion

**Filtering Options:**
```
Start Date: [Filter from date]
End Date: [Filter to date]
Product Type: [All | Ointment | Tablet | Capsule]
Status: [All | Draft | Approved | In Production]
```

### 8.6 Comments & Observations Report

**Access:** Reports → Comments Report

**Purpose:** Consolidate all comments from:
- BMR creation (QA comments)
- Phase execution (Operator comments)
- Quality control (QC comments)
- Regulatory review (Regulatory comments)

**Filter Options:**
```
BMR Number: [Select specific BMR or All]
Comment Type: [All | BMR | Phase | QC | QA]
Date Range: [From date] to [To date]
User Role: [All | QA | QC | Operators | etc.]
```

**Report Displays:**
- BMR number
- Product name
- Comment type
- Phase (if applicable)
- Date of comment
- User who made comment
- Comment text
- Status

**View Options:**
- Table view (on screen)
- Export to Word
- Export to Excel
- Export to CSV

### 8.7 Production Timeline Reports

**Access:** Reports → Timeline Overview

**Comprehensive Timeline Analysis:**
- All BMRs with phase details
- Phase-by-phase breakdown
- Duration for each phase
- Operator assigned
- Machine used
- Quality checkpoints

**Summary Statistics:**
- Total BMRs in report
- Completed vs In Progress
- Average cycle time
- Longest phase durations
- Bottleneck identification

**Detailed Phase Information:**
For each BMR, shows:
- Phase name
- Status
- Started date/time
- Completed date/time
- Duration (hours)
- Operator
- Machine used
- Comments
- QC results (if applicable)

---

**[Screenshot Placeholder: Monthly Production Analytics Dashboard]**
*Caption: Monthly analytics showing charts and key metrics*

**[Screenshot Placeholder: BMR Timeline Tracking View]**
*Caption: Visual timeline with color-coded phase status*

**[Screenshot Placeholder: WIP Report with Filters]**
*Caption: Work in progress report showing active batches*

**[Screenshot Placeholder: Comments Report]**
*Caption: Consolidated comments report with filter options*

---

## 9. EXCEL & WORD EXPORT FEATURES

### 9.1 Export Features Overview

The system provides professional export capabilities for:
- **Excel (.xlsx)**: Detailed data with formatting, charts, multiple sheets
- **Word (.docx)**: Professional reports with company branding
- **CSV (.csv)**: Raw data for external analysis

### 9.2 Exporting Monthly Production to Excel

**Access:** Admin Dashboard → Production Analytics

**Step 1: Configure Report**
```
Month: [Select month]
Year: [Select year]
Product Type: [All or specific type]
```

**Step 2: Click "Export to Excel" Button**
- Located next to "View Analytics" button
- System generates comprehensive Excel file

**Excel File Contents:**

**Sheet 1: Production Summary**
- Company header with logo placeholder
- Report title and generation date
- Key production metrics table
- Monthly statistics summary

**Sheet 2: Product Breakdown (if type filter applied)**
- Detailed product-by-product analysis
- Batch counts
- Unit totals
- Performance metrics

**Sheet 3: Batch Details**
- Complete list of all batches
- Batch number, product, size, status
- Dates (created, started, completed)
- Duration analysis

**Sheet 4: Weekly Analysis**
- Week-by-week breakdown
- Production trends
- Comparison charts

**Sheet 5: Daily Details**
- Day-by-day production
- Daily batch counts
- Daily unit totals

**Formatting Features:**
- Professional color scheme (Blue headers)
- Company branding
- Auto-sized columns
- Formatted numbers (thousand separators)
- Borders and cell styling
- Print-ready layout

**File Naming:**
```
Format: KPI_Production_Report_[Month]_[Year].xlsx
Example: KPI_Production_Report_November_2025.xlsx

With product filter:
Format: KPI_[Type]_Production_Report_[Month]_[Year].xlsx
Example: KPI_Tablet_Production_Report_November_2025.xlsx
```

### 9.3 Exporting BMR Timeline to Excel

**Access:** Admin Dashboard → BMR Timeline Tracking

**Click:** "Export Excel" button

**Excel File Contents:**

**Sheet 1: Production Summary**
- Lists all BMRs with summary information
- Batch number, product, type
- Request date, created date
- Current status and phase
- Total duration
- Completion status
- Bottleneck phase identification

**Sheets 2-N: Detailed BMR Timelines**
- One sheet per BMR
- Sheet name: "BMR-[BatchNumber]"
- Complete phase-by-phase breakdown

**Each BMR Sheet Contains:**
```
- BMR/Product information header
- Complete phase listing
- Phase status, dates, durations
- Operator information
- Machine used (if applicable)
- Comments from each phase
- QC results
- Breakdown/changeover times
```

**File Naming:**
```
Format: KPI_BMR_Timeline_Report_[Date].xlsx
Example: KPI_BMR_Timeline_Report_2025-12-03.xlsx
```

### 9.4 Exporting Comments to Word

**Access:** Reports → Comments Report

**Click:** "Export to Word" button

**Word Document Contents:**

**Header:**
```
KAMPALA PHARMACEUTICAL INDUSTRIES
Comments & Observations Report
Generated on: [Date and Time]
Report prepared by: [Your Name]
Total BMRs with comments: [Count]
```

**Body:**
- Organized by BMR
- Each BMR section includes:
  - BMR number and product name
  - Table of all comments:
    - Phase
    - Comment Type
    - Date
    - Comments text

**Footer:**
```
Automatically generated report from KPI Operations System
```

**Formatting:**
- Professional document styling
- Company header (blue)
- Tables with borders
- Consistent fonts (Arial)
- Page breaks between BMRs
- Print-ready layout

**File Naming:**
```
Format: KPI_Comments_Report_[Timestamp].docx
Example: KPI_Comments_Report_20251203_143022.docx
```

### 9.5 Exporting Comments to Excel

**Access:** Reports → Comments Report

**Click:** "Export to Excel" button

**Excel File Contents:**

**Single Sheet: "Comments Report"**

**Columns:**
- BMR Number
- Product
- Comment Type
- Phase
- User (who made comment)
- User Role
- Date
- Comments
- Status

**Features:**
- Sortable columns
- Filterable data
- Formatted headers
- Auto-sized columns
- Thousands of rows supported

**File Naming:**
```
Format: KPI_Comments_Report_[Timestamp].xlsx
Example: KPI_Comments_Report_20251203_143022.xlsx
```

### 9.6 Exporting to CSV

**Available for:**
- BMR Timeline
- Comments Report
- Work in Progress
- Any data table

**Click:** "Export CSV" button

**CSV Format:**
- Comma-separated values
- UTF-8 encoding
- Header row with column names
- Compatible with Excel, Google Sheets, databases

**Use Cases:**
- Import into other systems
- Custom data analysis
- Database loading
- Third-party reporting tools

**File Naming:**
```
Format: KPI_[ReportType]_[Timestamp].csv
Examples:
- KPI_Timeline_20251203.csv
- KPI_Comments_20251203.csv
- KPI_WIP_20251203.csv
```

### 9.7 Export Best Practices

**Before Exporting:**
- Apply desired filters
- Set correct date ranges
- Select appropriate views
- Verify data completeness

**File Management:**
- Exports download to browser's download folder
- Rename files meaningfully
- Organize in folders by date/type
- Archive old reports regularly

**Performance Considerations:**
- Large exports (>1000 records) may take 10-30 seconds
- System shows "Generating..." message
- Don't click button multiple times
- Wait for download to complete

**Excel File Size:**
- Typical monthly report: 200-500 KB
- Timeline with 50 BMRs: 1-2 MB
- Comments report: 100-300 KB

---

**[Screenshot Placeholder: Export to Excel Button]**
*Caption: Location of export button in production analytics*

**[Screenshot Placeholder: Excel Report Example - Summary Sheet]**
*Caption: Excel production report showing formatted summary sheet*

**[Screenshot Placeholder: Word Report Example]**
*Caption: Word comments report with company branding*

**[Screenshot Placeholder: Download Notification]**
*Caption: Browser download notification for exported file*

---

## 10. DJANGO ADMIN INTERFACE - SUPERUSER GUIDE

### 10.1 Accessing Django Admin Panel

**URL:** `http://192.168.1.244:8000/admin/`

**Login Requirements:**
- Must have **Staff status** enabled
- OR **Superuser status** enabled
- Standard operators cannot access admin panel

**Login:**
```
Username: admin
Password: admin123 (change in production!)
```

### 10.2 Django Admin Overview

**Left Sidebar Sections:**
- **ACCOUNTS**: User management
- **BMR**: Batch Manufacturing Records
- **DASHBOARDS**: Dashboard settings and permissions
- **FGS_MANAGEMENT**: Finished Goods Store
- **PRODUCTS**: Product master data
- **QUARANTINE**: Quarantine management
- **WORKFLOW**: Production phases and settings

### 10.3 Managing All System Models

#### **ACCOUNTS Section**

**Custom Users:**
- **Purpose**: Complete user management
- **Actions**: Add, Edit, Delete, Reset passwords
- **Fields**: Username, email, role, permissions
- **Bulk Actions**: Reset passwords, activate/deactivate

**User Sessions:**
- **Purpose**: Active session tracking
- **View**: All logged-in users
- **Actions**: End sessions, view login times

#### **BMR Section**

**BMRs (Batch Manufacturing Records):**
- **Purpose**: View/edit all BMRs
- **Fields**: All BMR data
- **Actions**: Approve, reject, modify status
- **Search**: By batch number, product, status
- **Filters**: Status, product type, date range

**BMR Materials:**
- **Purpose**: Material requirements for BMRs
- **View**: Materials linked to each BMR
- **Edit**: Quantities, suppliers, lot numbers

**BMR Requests:**
- **Purpose**: Production manager requests
- **View**: All pending and processed requests
- **Actions**: Approve, reject, track status

**BMR Signatures:**
- **Purpose**: Electronic signature audit trail
- **View**: All signatures on BMRs
- **Read-only**: Compliance requirement
- **Audit**: Who signed, when, what action

#### **DASHBOARDS Section**

**Dashboard Metrics:**
- **Purpose**: System performance metrics
- **View**: Production statistics
- **Read-only**: Calculated data

**Dashboard Permissions:**
- **Purpose**: Control who sees which dashboards
- **Critical**: Covered in detail in Section 12
- **Actions**: Create, edit, delete permissions

**Notification Alerts:**
- **Purpose**: System notifications
- **View**: All alerts sent to users
- **Actions**: Create manual alerts, clear old alerts

**User Dashboard Preferences:**
- **Purpose**: User-specific dashboard settings
- **View**: Individual preferences
- **Edit**: Modify user dashboard configurations

#### **FGS_MANAGEMENT Section**

**Finished Goods Inventory:**
- **Purpose**: Track finished goods storage
- **Fields**: Product, quantity, location, dates
- **Actions**: Add, update stock levels

**Sales Orders:**
- **Purpose**: Customer order management
- **Fields**: Customer, product, quantity, dates
- **Actions**: Create orders, track fulfillment

**Sales Order Items:**
- **Purpose**: Line items within sales orders
- **View**: Individual products in each order

#### **PRODUCTS Section**

**Products:**
- **Purpose**: Product master data management
- **Critical**: Must be configured before BMR creation
- **Actions**: Add products, edit configurations
- **Covered**: Detailed in Section 3

**Product Ingredients:**
- **Purpose**: Ingredient/BOM management
- **Fields**: Ingredient name, quantity, supplier
- **Optional**: Used for material planning

**Product Specifications:**
- **Purpose**: Quality specifications
- **Fields**: Test parameters, acceptance criteria
- **Optional**: Reference for QC

#### **QUARANTINE Section**

**Quarantine Batches:**
- **Purpose**: Batches held in quarantine
- **View**: All quarantined batches
- **Status**: Track quarantine lifecycle

**Sample Requests:**
- **Purpose**: QC sample requests
- **View**: All samples requested and tested
- **Actions**: View results, approve/reject

#### **WORKFLOW Section**

**Production Phases:**
- **Purpose**: Master list of all phase types
- **View**: Phase definitions
- **Read-only**: System-managed

**Product Workflow Templates:**
- **Purpose**: Define workflow for each product type
- **View**: Phase sequences
- **Edit**: Custom workflow configurations

**Batch Phase Executions:**
- **Purpose**: Actual phase executions for BMRs
- **Critical**: Complete production history
- **View**: All phase data, operators, machines, times
- **Search**: By batch, phase, operator

**Machines:**
- **Purpose**: Equipment master data
- **Fields**: Machine name, type, capacity
- **Actions**: Add machines, update status

**Admin Settings (4 Categories):**

1. **Dashboard Settings**
   - Page size, refresh intervals
   - Display options
   - 17 configurable parameters

2. **System Alert Settings**
   - Alert thresholds
   - Notification rules
   - 15 configurable parameters

3. **Session Management Settings**
   - Timeout durations
   - Security settings
   - 15 configurable parameters

4. **Production Limits Settings**
   - Capacity limits
   - Quality limits
   - 15 configurable parameters

**Total: 62 system configuration parameters**

### 10.4 Common Admin Tasks

#### **Task 1: Add New User**

```
1. Admin Panel → ACCOUNTS → Custom Users
2. Click "+ Add User"
3. Enter username and password (twice)
4. Click "Save and continue editing"
5. Fill in personal info (name, email)
6. SELECT ROLE (most important!)
7. Check "Active" box
8. Check "Staff status" if admin access needed
9. Check "Superuser status" for full access
10. Click "Save"
```

#### **Task 2: Reset User Password**

```
Method A: Individual Reset
1. ACCOUNTS → Custom Users
2. Click on username
3. Click "this form" link next to password
4. Enter new password twice
5. Click "Change password"

Method B: Bulk Reset
1. ACCOUNTS → Custom Users
2. Select multiple users (checkboxes)
3. Action dropdown: "Reset passwords to default (role123)"
4. Click "Go"
5. Passwords reset to: [role]123
```

#### **Task 3: Add New Product**

```
1. Admin Panel → PRODUCTS → Products
2. Click "+ Add Product"
3. Product name: [Full name]
4. Product type: [ointment|tablet|capsule]
5. If tablet: Set coating type and tablet type
6. Batch size: [Number]
7. Batch size unit: [tablets|capsules|tubes]
8. Check "Is active"
9. Click "Save"
```

#### **Task 4: Add New Machine**

```
1. Admin Panel → WORKFLOW → Machines
2. Click "+ Add Machine"
3. Machine name: [e.g., "Granulation Machine - GM001"]
4. Machine type: [Select from dropdown]
5. Capacity: [Optional - numeric value]
6. Check "Is active"
7. Click "Save"
```

#### **Task 5: View BMR Complete History**

```
1. Admin Panel → BMR → BMRs
2. Find BMR by batch number (search box)
3. Click on batch number
4. View all BMR details
5. Click "Batch Phase Executions" to see production history
```

#### **Task 6: Manually Approve BMR (Emergency)**

```
1. Admin Panel → BMR → BMRs
2. Find BMR
3. Click to edit
4. Change status dropdown:
   - draft → submitted (if QA forgot)
   - submitted → approved (if regulatory approval needed)
5. Click "Save"

⚠️ Warning: Only for emergencies. Follow normal workflow!
```

#### **Task 7: Clear Old Notifications**

```
1. Admin Panel → DASHBOARDS → Notification Alerts
2. Filter by date (older than X days)
3. Select all (checkbox at top)
4. Action: "Delete selected notification alerts"
5. Click "Go"
6. Confirm deletion
```

#### **Task 8: View System Audit Trail**

```
For BMR Actions:
1. BMR → BMR Signatures
2. Shows all electronic signatures
3. Who did what, when

For Phase Actions:
1. WORKFLOW → Batch Phase Executions
2. Filter by BMR or operator
3. View complete phase history
4. Export if needed

For User Actions:
1. ACCOUNTS → User Sessions
2. View login activity
3. Track active sessions
```

### 10.5 Admin Panel Search and Filters

**Search Functionality:**
- Search box at top of each list view
- Searches relevant fields automatically
- Case-insensitive
- Partial matches supported

**Filter Sidebar:**
- Right side of list views
- Quick filters by common criteria
- Examples:
  - BMRs: Filter by status, product type, date
  - Users: Filter by role, active status
  - Machines: Filter by type, active status

**Advanced Filtering:**
- Use filter icon (if available)
- Combine multiple filter criteria
- Save filter combinations

### 10.6 Bulk Actions

**Available Bulk Actions:**
- Select multiple items (checkboxes)
- Choose action from dropdown
- Click "Go" to execute

**Common Bulk Actions:**
- Delete selected items
- Reset passwords (users)
- Change status (various models)
- Export selected items

**⚠️ Caution:**
- Bulk delete is permanent
- No undo for bulk actions
- Always verify selection before executing

### 10.7 Admin Panel Best Practices

**DO:**
- ✅ Use search before browsing large lists
- ✅ Apply filters to narrow results
- ✅ Read confirmation messages
- ✅ Test changes in development first
- ✅ Keep browser tab open for reference

**DON'T:**
- ❌ Delete records without verification
- ❌ Change status without understanding impact
- ❌ Modify system-managed fields
- ❌ Make bulk changes without backup
- ❌ Share admin credentials

**Security:**
- Always logout when finished
- Use strong admin password
- Limit superuser accounts
- Regular audit of admin actions
- Review user permissions quarterly

### 10.8 Admin Panel URLs Reference

Quick access URLs:
```
Main Admin: http://192.168.1.244:8000/admin/

Users: /admin/accounts/customuser/
BMRs: /admin/bmr/bmr/
Products: /admin/products/product/
Machines: /admin/workflow/machine/
Phases: /admin/workflow/batchphaseexecution/
Quarantine: /admin/quarantine/quarantinebatch/
Dashboard Permissions: /admin/dashboards/dashboardpermission/
Settings: /admin/workflow/dashboardsettings/
```

---

**[Screenshot Placeholder: Django Admin Home]**
*Caption: Django admin panel homepage showing all sections*

**[Screenshot Placeholder: User Management List]**
*Caption: User list with search, filters, and bulk actions*

**[Screenshot Placeholder: Add User Form]**
*Caption: User creation form with role dropdown highlighted*

**[Screenshot Placeholder: BMR Detail in Admin]**
*Caption: BMR detail view showing all editable fields*

**[Screenshot Placeholder: Batch Phase Execution List]**
*Caption: Complete phase execution history with filters*

---

## 11. SYSTEM CONFIGURATION & SETTINGS

### 11.1 Accessing System Settings

**Path:** Django Admin → WORKFLOW → (Select settings category)

Four categories with 62 total configurable parameters:
1. Dashboard Settings (17 parameters)
2. System Alert Settings (15 parameters)
3. Session Management Settings (15 parameters)
4. Production Limits Settings (15 parameters)

### 11.2 Dashboard Settings (17 Parameters)

**Access:** Admin → WORKFLOW → Dashboard Settings

**Performance Settings:**
```
page_size: 25
  - Number of items per page in lists
  - Range: 10-100
  - Higher = fewer page loads, slower initial load

refresh_interval: 30
  - Dashboard auto-refresh in seconds
  - Range: 15-300
  - Lower = more real-time, higher server load

chart_animation: true
  - Enable/disable chart animations
  - True: Better UX, slight performance cost
  - False: Faster rendering
```

**Display Settings:**
```
show_progress_bars: true
  - Show phase progress indicators
  
show_phase_durations: true
  - Display time taken for each phase

compact_view: false
  - Dense layout vs spacious layout

show_machine_status: true
  - Display machine status indicators

show_analytics_widgets: true
  - Show dashboard analytics widgets
```

**Functionality Settings:**
```
enable_quick_actions: true
  - Quick action buttons on cards

enable_bulk_operations: true
  - Allow bulk actions on lists

auto_save_drafts: true
  - Auto-save forms periodically

enable_advanced_filters: true
  - Complex filtering options

cache_dashboard_data: true
  - Cache for performance
```

**Notification Settings:**
```
show_realtime_updates: true
  - Live dashboard updates

enable_sound_alerts: false
  - Audio notifications

popup_notifications: true
  - Browser popup alerts
```

**Advanced Settings:**
```
export_batch_limit: 1000
  - Max records per export
  - Range: 100-10000
```

**To Modify:**
1. Click on "Dashboard Settings" (only 1 row exists)
2. Change values as needed
3. Click "Save"
4. Changes apply immediately (no restart needed)

### 11.3 System Alert Settings (15 Parameters)

**Access:** Admin → WORKFLOW → System Alert Settings

**Alert Timing:**
```
phase_warning_threshold: 80
  - Warning at 80% of expected time
  - Range: 50-100

phase_overrun_threshold: 120
  - Critical alert at 120% of expected time
  - Range: 100-200

batch_delay_threshold: 24
  - Hours before batch delay alert
  - Range: 1-72
```

**Machine Alerts:**
```
breakdown_alert_enabled: true
  - Send alerts on machine breakdown

maintenance_reminder_days: 7
  - Days before maintenance due
  - Range: 1-30

utilization_warning_threshold: 90
  - Alert when utilization exceeds %
  - Range: 70-100
```

**Quality Alerts:**
```
qc_failure_alert_enabled: true
  - Alert on QC test failures

quarantine_alert_enabled: true
  - Alert when batch quarantined

deviation_alert_enabled: true
  - Alert on process deviations
```

**Inventory Alerts:**
```
low_stock_threshold: 10
  - Low stock warning level
  - Range: 1-100

expiry_warning_days: 30
  - Days before material expiry
  - Range: 7-90
```

**System Alerts:**
```
system_performance_monitoring: true
  - Monitor system performance

database_backup_alerts: true
  - Alert on backup status

security_alert_enabled: true
  - Security event notifications

error_notification_enabled: true
  - System error alerts
```

### 11.4 Session Management Settings (15 Parameters)

**Access:** Admin → WORKFLOW → Session Management Settings

**Session Security:**
```
session_timeout_minutes: 30
  - Inactivity timeout
  - Range: 5-240
  - Recommended: 30-60

max_concurrent_sessions: 3
  - Max sessions per user
  - Range: 1-10
  - Prevents credential sharing

force_logout_on_timeout: true
  - Auto-logout vs warning
```

**Password Security:**
```
password_expiry_days: 90
  - Password expires after days
  - Range: 30-365
  - 0 = never expires

min_password_length: 8
  - Minimum characters
  - Range: 6-20

require_password_complexity: true
  - Require mixed case, numbers, special chars
```

**Login Security:**
```
max_failed_attempts: 3
  - Account lockout threshold
  - Range: 3-10

lockout_duration_minutes: 15
  - Account lock duration
  - Range: 5-60

require_2fa_admin: false
  - Two-factor authentication for admins
  - Not implemented yet (future feature)
```

**Audit & Compliance:**
```
log_user_actions: true
  - Log all user actions

audit_trail_retention_days: 365
  - Keep logs for days
  - Range: 90-1825 (5 years)
```

**Session Management:**
```
remember_login_days: 7
  - "Remember me" duration
  - Range: 1-30

idle_warning_minutes: 25
  - Show warning before timeout
  - Should be < session_timeout_minutes

auto_save_interval_seconds: 300
  - Auto-save forms every X seconds
  - Range: 60-600

cleanup_expired_sessions: true
  - Auto-delete old sessions
```

### 11.5 Production Limits Settings (15 Parameters)

**Access:** Admin → WORKFLOW → Production Limits Settings

**Capacity Limits:**
```
max_concurrent_batches: 50
  - Maximum active BMRs
  - Range: 10-200

max_batch_size: 100000
  - Maximum batch size allowed
  - Range: 100-1000000

max_daily_production: 10
  - Max batches per day
  - Range: 1-50
```

**Quality Limits:**
```
max_qc_samples_per_batch: 2
  - Maximum samples per quarantine
  - Range: 1-5
  - Current: 2 (system enforced)

max_quarantine_duration_hours: 168
  - Maximum time in quarantine (7 days)
  - Range: 24-720

quality_hold_time_hours: 72
  - Standard quality hold time
  - Range: 24-168
```

**Performance Limits:**
```
max_phase_duration_hours: 48
  - Warning if phase exceeds
  - Range: 1-168

breakdown_tolerance_minutes: 120
  - Max acceptable breakdown time
  - Range: 30-480

changeover_time_limit_minutes: 60
  - Max acceptable changeover time
  - Range: 15-240
```

**Resource Limits:**
```
max_operators_per_phase: 3
  - Max operators assigned to phase
  - Range: 1-10

max_machine_utilization: 95
  - Maximum utilization % before warning
  - Range: 70-100
```

**Data Limits:**
```
max_export_records: 10000
  - Maximum records per export
  - Range: 100-100000

max_report_range_days: 90
  - Max date range for reports
  - Range: 7-365

max_file_upload_size_mb: 10
  - Max file upload size
  - Range: 1-100

database_cleanup_days: 1095
  - Data retention (3 years)
  - Range: 365-3650
```

### 11.6 Configuration Best Practices

**Before Changing Settings:**
- ✅ Document current values
- ✅ Understand impact of change
- ✅ Test in development first
- ✅ Change during off-peak hours
- ✅ Monitor system after change

**Recommended Values (Production):**
```
session_timeout_minutes: 30
max_concurrent_sessions: 3
password_expiry_days: 90
max_qc_samples_per_batch: 2
phase_warning_threshold: 80
audit_trail_retention_days: 1095 (3 years for GMP)
```

**Performance Tuning:**
```
High-load environment:
- refresh_interval: 60 (reduce frequency)
- page_size: 50 (larger pages, fewer requests)
- cache_dashboard_data: true

Low-traffic environment:
- refresh_interval: 15 (more real-time)
- page_size: 25 (standard)
- cache_dashboard_data: false
```

### 11.7 Hot Configuration (No Restart Required)

**All settings apply immediately:**
- No server restart needed
- Changes effective on next page load
- Users don't need to re-login
- Dashboard updates automatically

**Exception:**
- Session timeout applies to NEW sessions
- Existing sessions keep original timeout

---

**[Screenshot Placeholder: Dashboard Settings Admin]**
*Caption: Dashboard settings configuration with all 17 parameters*

**[Screenshot Placeholder: Session Management Settings]**
*Caption: Session and security settings configuration*

**[Screenshot Placeholder: Production Limits Settings]**
*Caption: Production capacity and quality limits configuration*

---

## 12. DASHBOARD PERMISSIONS MANAGEMENT

### 12.1 Dashboard Permission System Overview

Control which users can access which dashboard features based on:
- ✅ User role (e.g., "qa", "admin", "production_manager")
- ✅ Individual user exceptions (allow/block specific users)
- ✅ System requirements (staff, superuser status)

### 12.2 Accessing Dashboard Permissions

**Path:** Django Admin → DASHBOARDS → Dashboard Permissions

**What You'll See:**
- List of all controllable dashboard features
- Permission names (e.g., "system_health", "user_management")
- Allowed roles
- System requirements
- Active status

### 12.3 Permission Check Logic

System checks permissions in this order:

**Step 1: Check if blocked**
```
If user in "Blocked Users" → Access DENIED
Exit immediately
```

**Step 2: Check if explicitly allowed**
```
If user in "Allowed Users" → Access GRANTED
Exit immediately
```

**Step 3: Check system requirements**
```
If requires_superuser AND user not superuser → Access DENIED
If requires_staff AND user not staff → Access DENIED
```

**Step 4: Check role**
```
If user.role in allowed_roles → Access GRANTED
Otherwise → Access DENIED
```

### 12.4 Key Dashboard Permissions

**Admin Dashboard Sections:**

**system_health**
- Controls: System Health monitoring section
- Default: Superuser only
- Used for: Server status, database, performance

**system_logs**
- Controls: System logs viewer
- Default: Superuser only
- Used for: Error logs, audit logs

**user_management**
- Controls: User management links
- Default: Superuser and admin role
- Used for: Create/edit users, permissions

**machine_management**
- Controls: Machine management section
- Default: Admin, production_manager
- Used for: Add/edit machines, view status

**quality_control**
- Controls: Quality control dashboard features
- Default: QC, QA, admin roles
- Used for: QC testing, results entry

**inventory**
- Controls: Inventory management features
- Default: Store_manager, admin roles
- Used for: Material tracking, stock levels

**phase_notifications**
- Controls: Notifications & Alerts sidebar section
- Default: QA, admin, production_manager
- Used for: Phase alerts, system notifications

**quarantine**
- Controls: Quarantine tracking sidebar section
- Default: Quarantine manager, QC, QA, admin
- Used for: Quarantine batch management

### 12.5 Creating/Editing Dashboard Permissions

**To Create New Permission:**
```
1. Admin → DASHBOARDS → Dashboard Permissions
2. Click "+ Add Dashboard Permission"
3. Fill in fields (see below)
4. Click "Save"
```

**To Edit Existing Permission:**
```
1. Admin → DASHBOARDS → Dashboard Permissions
2. Click on permission name
3. Modify fields
4. Click "Save"
```

**Field Details:**

**Name (identifier):**
```
Format: lowercase_with_underscores
Examples: system_health, user_management, phase_notifications
Used in code: check_dashboard_permission(user, 'system_health')
Cannot change after creation!
```

**Description:**
```
Human-readable explanation
Example: "Access to system health monitoring and performance metrics"
Helps administrators understand what this controls
```

**Is Active:**
```
☑ Checked: Permission enforced
☐ Unchecked: Permission bypassed (all users can access)
Use to temporarily disable permission checking
```

**System Requirements:**

**Requires Staff:**
```
☑ Checked: Only staff users can access
☐ Unchecked: Any user can access (if other checks pass)
Staff = Can access Django Admin
```

**Requires Superuser:**
```
☑ Checked: Only superusers can access
☐ Unchecked: Any user can access (if other checks pass)
Superuser = Full system access
```

**Allowed Roles (JSON Array):**
```
Format: ["role1", "role2", "role3"]

Examples:
All admins and QA:
["admin", "qa"]

Only QC:
["qc"]

Multiple production roles:
["production_manager", "qa", "admin"]

No roles (superuser only):
[]

Widget: Textarea (enter JSON manually)
Validation: Must be valid JSON array
```

**User-Specific Overrides:**

**Allowed Users (Multi-select):**
```
Select specific users who CAN access
Regardless of their role
Overrides role restrictions
Example use: Give access to specific QA user temporarily
```

**Blocked Users (Multi-select):**
```
Select specific users who CANNOT access
Regardless of their role or allowed_users
Takes precedence over everything
Example use: Temporarily revoke access from problematic user
```

### 12.6 Example Permission Configurations

**Example 1: System Health (Superuser Only)**
```
Name: system_health
Description: System health monitoring and server status
Is Active: ☑ Checked
Requires Staff: ☐ Unchecked
Requires Superuser: ☑ Checked
Allowed Roles: []
Allowed Users: (none)
Blocked Users: (none)

Result: Only superusers see System Health section
```

**Example 2: User Management (Admin Role + Superuser)**
```
Name: user_management
Description: User account management and permissions
Is Active: ☑ Checked
Requires Staff: ☐ Unchecked
Requires Superuser: ☐ Unchecked
Allowed Roles: ["admin"]
Allowed Users: (none)
Blocked Users: (none)

Result: Users with role="admin" OR superusers can access
```

**Example 3: Quality Control (Multiple Roles)**
```
Name: quality_control
Description: QC testing and quality management features
Is Active: ☑ Checked
Requires Staff: ☐ Unchecked
Requires Superuser: ☐ Unchecked
Allowed Roles: ["qc", "qa", "admin"]
Allowed Users: (none)
Blocked Users: (none)

Result: QC, QA, Admin roles can access
```

**Example 4: Specific User Exception**
```
Name: machine_management
Description: Machine and equipment management
Is Active: ☑ Checked
Requires Staff: ☐ Unchecked
Requires Superuser: ☐ Unchecked
Allowed Roles: ["admin", "production_manager"]
Allowed Users: [Select: john_doe (Equipment Operator)]
Blocked Users: (none)

Result: Admins, production managers, AND user "john_doe" can access
```

**Example 5: Blocking Specific User**
```
Name: phase_notifications
Description: Phase notifications and alerts
Is Active: ☑ Checked
Requires Staff: ☐ Unchecked
Requires Superuser: ☐ Unchecked
Allowed Roles: ["qa", "admin", "production_manager"]
Allowed Users: (none)
Blocked Users: [Select: jane_smith (QA)]

Result: QA, admins, production managers EXCEPT jane_smith can access
```

### 12.7 Sidebar Section Visibility

**How Sidebar Sections Work:**

**Overview Section:**
- Always visible (core functionality)
- Cannot be hidden

**Production Management Section:**
- Shows if user has access to ANY of:
  - machine_management
  - quality_control
  - inventory
- If all three denied → section hidden

**Quarantine Tracking Section:**
- Shows if user has access to:
  - quarantine permission
- Currently always visible, can be controlled

**Notifications & Alerts Section:**
- Shows if user has access to:
  - phase_notifications permission

**System Administration Section:**
- Shows if user has access to ANY of:
  - system_health
  - system_logs
  - user_management
- If all three denied → section hidden entirely

### 12.8 Testing Dashboard Permissions

**After Configuration:**

**Step 1: Login as Test User**
- Use user account with specific role
- Navigate to dashboard

**Step 2: Verify Sidebar**
- Check which sections appear
- Verify expected sections visible
- Confirm restricted sections hidden

**Step 3: Test Links**
- Click on visible sections
- Verify access granted
- Try accessing restricted features via URL (should be blocked)

**Step 4: Test Edge Cases**
- Blocked user override
- Allowed user override
- Multiple role scenarios

### 12.9 Common Permission Scenarios

**Scenario 1: Hide System Administration from Regular Admins**
```
Goal: Only superusers see System Administration section

Configuration:
- system_health: requires_superuser = true
- system_logs: requires_superuser = true
- user_management: requires_superuser = true

Result: Regular admins don't see System Administration section
```

**Scenario 2: QA Can See Everything Except System Admin**
```
Goal: QA has full access except system settings

Configuration:
- All permissions: allowed_roles includes "qa"
- EXCEPT: system_health, system_logs (superuser only)

Result: QA sees Production, Quarantine, Notifications but not System Admin
```

**Scenario 3: Production Manager Limited Access**
```
Goal: Production manager sees only production features

Configuration:
- machine_management: allowed_roles = ["production_manager", "admin"]
- inventory: allowed_roles = ["store_manager", "admin"]
  (production_manager NOT included)
- quality_control: allowed_roles = ["qc", "qa", "admin"]
  (production_manager NOT included)

Result: Production manager sees machine management only
```

### 12.10 Permission Troubleshooting

**Problem: User can't see expected section**

**Check:**
1. User role correctly assigned? (Admin → Users → View user)
2. Permission has correct role in allowed_roles?
3. User not in blocked_users?
4. Permission is_active = true?
5. System requirements met (staff/superuser)?

**Problem: User sees restricted section**

**Check:**
1. User in allowed_users? (override)
2. User is superuser? (bypasses most checks)
3. Permission is_active = false? (disabled)
4. Correct permission name used in view?

**Problem: Allowed_roles not saving**

**Solution:**
- Ensure JSON format: ["role1", "role2"]
- Use double quotes, not single quotes
- No trailing commas
- Check admin form for errors

---

**[Screenshot Placeholder: Dashboard Permissions List]**
*Caption: List of all dashboard permissions in admin panel*

**[Screenshot Placeholder: Edit Dashboard Permission Form]**
*Caption: Edit permission form showing all fields and user selection*

**[Screenshot Placeholder: Allowed Roles JSON Field]**
*Caption: Textarea showing correct JSON format for roles*

**[Screenshot Placeholder: Sidebar with Limited Access]**
*Caption: Dashboard sidebar showing only permitted sections*

---

## 13. TROUBLESHOOTING & SUPPORT

### 13.1 Common Login Issues

**Problem: Cannot access login page**
```
Symptoms: Page won't load, timeout errors

Solutions:
1. Check network connection
2. Verify server is running (IT)
3. Try different browser
4. Clear browser cache and cookies
5. Check if firewall blocking access
6. Verify correct URL: http://192.168.1.244:8000
```

**Problem: Invalid credentials error**
```
Symptoms: "Invalid username or password" message

Solutions:
1. Verify username (case-sensitive)
2. Check password (check Caps Lock)
3. Try default password: [role]123
4. Contact admin for password reset
5. Check if account is active (Admin → Users)
6. Check if account is locked (too many failed attempts)
```

**Problem: Login successful but blank dashboard**
```
Symptoms: After login, blank page or no content

Solutions:
1. Wait 10-15 seconds (slow network)
2. Refresh page (F5 or Ctrl+R)
3. Clear browser cache completely
4. Check browser console for errors (F12)
5. Try different browser
6. Verify user has correct role assigned
7. Check dashboard permissions configuration
```

**Problem: Session timeout too frequent**
```
Symptoms: Logged out every few minutes

Solutions:
1. Check session_timeout_minutes setting (Admin → Workflow → Session Settings)
2. Increase timeout value (current: 30 minutes)
3. Use "Remember Me" option at login (if available)
4. Check for browser security software blocking cookies
5. Verify system clock synchronization
```

### 13.2 BMR Creation Issues

**Problem: Cannot create BMR - Product dropdown empty**
```
Solutions:
1. Verify products exist (Admin → Products)
2. Check products have is_active = true
3. Refresh page
4. Clear browser cache
5. Check user has QA role
```

**Problem: Batch number validation error**
```
Symptoms: "Invalid batch number format" or "Batch number already exists"

Solutions:
1. Verify format: XXXYYYY (7 digits)
   Example: 0012025, not 12025 or 00012025
2. Check for duplicate (search existing BMRs)
3. Use next sequential number
4. Contact QA manager if number conflict
```

**Problem: BMR stuck in Draft status**
```
Solutions:
1. Complete all required fields
2. Click "Submit for Approval" not just "Save"
3. Check for validation errors (red text)
4. Verify material requirements added
5. Check manufacturing instructions completed
```

**Problem: Regulatory cannot find BMR to approve**
```
Solutions:
1. Verify BMR status = "Submitted"
2. Check if regulatory user logged in
3. Refresh dashboard
4. Search by batch number
5. Admin can manually change status if needed
```

### 13.3 Production Phase Issues

**Problem: Phase not appearing in operator dashboard**
```
Solutions:
1. Verify previous phase completed
2. Check user role matches phase requirement
   Example: Mixing phase needs mixing_operator role
3. Verify BMR status = "Approved"
4. Check if batch in quarantine
5. Refresh dashboard
6. Contact supervisor
```

**Problem: Cannot start phase - machine required**
```
Symptoms: "Please select a machine" error

Solutions:
1. Check if machines exist for this type (Admin → Machines)
2. Verify machines have is_active = true
3. Add machines if none available (Admin access)
4. Contact equipment manager
```

**Problem: Phase complete button not working**
```
Solutions:
1. Fill all required fields (completion comments)
2. Answer breakdown/changeover questions
3. Check for JavaScript errors (F12 console)
4. Try different browser
5. Refresh page and try again
6. Contact IT support
```

**Problem: Completed phase not triggering next phase**
```
Solutions:
1. Check if QC checkpoint required (automatic quarantine)
2. Wait a few seconds and refresh
3. Verify phase completed successfully (check status)
4. Contact QA/Admin to check workflow configuration
5. Admin can manually advance phase if needed
```

### 13.4 Quality Control Issues

**Problem: Quarantined batch not showing in QC dashboard**
```
Solutions:
1. Verify sample requested by quarantine manager
2. Check QA has taken sample
3. Confirm sample sent to QC
4. Refresh dashboard
5. Check if sample already processed
```

**Problem: Cannot approve/reject sample**
```
Solutions:
1. Verify test results entered
2. Fill all required fields
3. Check user has QC role
4. Ensure sample received by QC
5. Refresh page
6. Contact QC manager
```

**Problem: Batch not releasing from quarantine after approval**
```
Solutions:
1. Verify sample status = "Approved"
2. Quarantine manager must click "Release Batch"
3. Check if multiple samples requested (all must be complete)
4. Refresh quarantine dashboard
5. Admin can manually release if needed
```

### 13.5 Report and Export Issues

**Problem: Export button not working**
```
Solutions:
1. Check browser popup blocker
2. Allow downloads from this site
3. Wait for file generation (large exports take time)
4. Check browser download folder
5. Try different export format (Excel vs CSV)
6. Reduce date range/filter data
```

**Problem: Export file empty or corrupted**
```
Solutions:
1. Verify data exists for selected filters
2. Check date range includes data
3. Try smaller date range
4. Re-download file
5. Try different browser
6. Contact IT support
```

**Problem: Timeline report shows no data**
```
Solutions:
1. Verify BMRs exist in date range
2. Check BMR approval status
3. Ensure phases have been executed
4. Clear filters and try again
5. Refresh page
```

### 13.6 Performance Issues

**Problem: Slow dashboard loading**
```
Solutions:
1. Clear browser cache
2. Close unnecessary browser tabs
3. Check network connection speed
4. Reduce dashboard refresh_interval (Admin → Settings)
5. Disable chart_animation (Admin → Settings)
6. Contact IT to check server load
7. Schedule heavy tasks (exports) during off-peak hours
```

**Problem: Report generation timeout**
```
Solutions:
1. Reduce date range (try 1 month instead of 6)
2. Use specific filters (product type, status)
3. Export in batches
4. Schedule report during off-hours
5. Contact admin to increase max_export_records limit
6. Use CSV instead of Excel for large datasets
```

**Problem: Page unresponsive or frozen**
```
Solutions:
1. Wait 30-60 seconds (may be processing)
2. Check browser task manager (Shift+Esc in Chrome)
3. Close other tabs
4. Refresh page (may lose unsaved data)
5. Clear browser cache
6. Try incognito/private mode
7. Restart browser
```

### 13.7 Django Admin Panel Issues

**Problem: Cannot access admin panel**
```
Symptoms: 404 error or access denied

Solutions:
1. Verify URL correct: /admin/ (with trailing slash)
2. Check user has staff status (Admin must enable)
3. Verify user active
4. Use superuser account for testing
5. Contact system administrator
```

**Problem: Models not visible in admin**
```
Solutions:
1. Verify staff/superuser status
2. Check permissions assigned
3. Models may not be registered in admin
4. Refresh page
5. Clear browser cache
```

**Problem: Cannot save changes in admin**
```
Solutions:
1. Check all required fields filled
2. Look for validation errors (red text)
3. Verify permissions to edit
4. Check for duplicate values (unique fields)
5. Review browser console for errors
```

### 13.8 Dashboard Permission Issues

**Problem: Cannot see expected dashboard sections**
```
Solutions:
1. Check user role (Admin → Users → view user)
2. Verify dashboard permissions (Admin → Dashboards → Dashboard Permissions)
3. Check if user in blocked_users
4. Verify permission is_active = true
5. Check allowed_roles includes user's role
6. Contact administrator
```

**Problem: Can see restricted sections**
```
Solutions:
1. Check if user in allowed_users (override)
2. Verify user not superuser (bypasses checks)
3. Check permission is_active status
4. Review permission configuration
5. Contact administrator to review permissions
```

### 13.9 System Error Messages

**Error: "CSRF verification failed"**
```
Cause: Security token expired or missing

Solutions:
1. Refresh the page
2. Clear cookies for this site
3. Re-login
4. Check if cookies enabled in browser
5. Try different browser
```

**Error: "Database locked"**
```
Cause: SQLite database locked by another process

Solutions:
1. Wait 10-20 seconds and retry
2. Refresh page
3. Contact IT to restart server
4. Admin: check for long-running queries
```

**Error: "Server error (500)"**
```
Cause: Internal server error

Solutions:
1. Refresh page
2. Try again in a few minutes
3. Check if server running (IT)
4. Contact administrator
5. Admin: check server logs
```

**Error: "Permission denied"**
```
Cause: User lacks required permissions

Solutions:
1. Verify user role correct
2. Check dashboard permissions
3. Contact administrator for access
4. May need different user role
```

### 13.10 Getting Help

**Self-Help Resources:**
- This user guide
- System tooltips and help text
- Previous similar transactions (view history)

**Contact Support:**

**For Technical Issues:**
- **IT Support**: it@kampalapharma.com
- **System Administrator**: admin@kampalapharma.com

**For Training Questions:**
- **Training Coordinator**: training@kampalapharma.com
- **QA Manager**: qa@kampalapharma.com

**For Production Issues:**
- **Production Manager**: production@kampalapharma.com
- **Operations Manager**: operations@kampalapharma.com

**Emergency Contact:**
- **24/7 Support Line**: +256-XXX-XXXX

**When Reporting Issues:**
Provide:
1. Your username and role
2. What you were trying to do
3. Exact error message (screenshot if possible)
4. Steps to reproduce the problem
5. Browser and version
6. Date and time of issue

**Log Files Location:**
```
Application Logs: ./logs/django.log
Error Logs: ./logs/error.log
User Activity: ./logs/user_activity.log
```

### 13.11 Preventive Maintenance

**Daily:**
- ✅ Logout when finished
- ✅ Save work frequently
- ✅ Report issues immediately

**Weekly:**
- ✅ Clear browser cache
- ✅ Check for system updates
- ✅ Review pending tasks

**Monthly:**
- ✅ Review and archive old reports
- ✅ Clean up downloads folder
- ✅ Update bookmarks if needed

---

**[Screenshot Placeholder: Error Message Example]**
*Caption: Common error message with explanation*

**[Screenshot Placeholder: Browser Console (F12)]**
*Caption: How to access browser console for debugging*

**[Screenshot Placeholder: Support Contact Information]**
*Caption: System support contact details*

---

## 14. APPENDIX

### 14.1 Glossary of Terms

**BMR**: Batch Manufacturing Record - Complete documentation of a manufacturing batch

**Batch Number**: Unique identifier format XXXYYYY (e.g., 0012025)

**Phase**: Individual step in production workflow

**Quarantine**: Holding status for batches awaiting quality approval

**QC**: Quality Control - Laboratory testing

**QA**: Quality Assurance - Quality oversight and final approval

**Operator**: Production personnel executing manufacturing phases

**Dashboard**: User-specific control panel

**Workflow**: Sequence of production phases

**Machine**: Equipment used in production phases

**GMP**: Good Manufacturing Practice - Regulatory compliance standards

### 14.2 Keyboard Shortcuts

**General:**
- `F5` or `Ctrl+R`: Refresh page
- `Ctrl+F`: Find on page
- `F12`: Open browser developer tools
- `Esc`: Close modal/dialog

**Forms:**
- `Tab`: Next field
- `Shift+Tab`: Previous field
- `Enter`: Submit form (some forms)
- `Ctrl+S`: Save (some forms)

### 14.3 System URLs Quick Reference

```
Main System: http://192.168.1.244:8000
Login: http://192.168.1.244:8000/accounts/login/
Admin Panel: http://192.168.1.244:8000/admin/
Dashboard: http://192.168.1.244:8000/dashboard/
BMR List: http://192.168.1.244:8000/bmr/list/
Reports: http://192.168.1.244:8000/reports/
Timeline: http://192.168.1.244:8000/reports/timeline/
```

### 14.4 Default User Credentials Summary

See Section 4.8 for complete list of all 24 user roles and default passwords.

**Pattern:** `[role]123`

Examples: `qa123`, `mixing123`, `admin123`

⚠️ **CHANGE ALL PASSWORDS IN PRODUCTION!**

### 14.5 System Capacity Specifications

- **Concurrent Users**: 50-200 (depending on server)
- **Max BMRs**: Unlimited (database dependent)
- **Phase Executions**: 1M+ records supported
- **Export Records**: Up to 10,000 per export (configurable)
- **File Upload Size**: 10 MB (configurable)

### 14.6 Backup and Recovery

**Automatic Backups:**
- Daily database backups (if configured)
- Backup location: Server administrator managed

**Manual Backup:**
- Export data regularly
- Save critical reports
- Archive completed BMRs

**Recovery:**
- Contact IT support immediately
- Provide backup date if known
- Be prepared for potential data loss since last backup

### 14.7 Security Recommendations

**For All Users:**
- ✅ Use strong, unique passwords
- ✅ Never share credentials
- ✅ Logout when finished
- ✅ Report security concerns immediately
- ✅ Don't access system from public computers

**For Administrators:**
- ✅ Regular user access reviews
- ✅ Disable inactive accounts
- ✅ Monitor failed login attempts
- ✅ Review audit logs weekly
- ✅ Keep system updated

**Production Deployment:**
- ✅ Change all default passwords
- ✅ Set DEBUG=False in settings.py
- ✅ Change SECRET_KEY in settings.py
- ✅ Use HTTPS in production
- ✅ Regular security audits

---

## 15. DOCUMENT INFORMATION

**Document Title:** Kampala Pharmaceutical Industries - Operations System Complete User Guide

**Version:** 1.0

**Date:** December 3, 2025

**Prepared For:** All KPI Operations System Users

**Prepared By:** System Documentation Team

**Document Type:** Training Manual & Technical Reference

**Scope:** Complete system functionality from basic login to advanced administration

**Audience:**
- Production operators (Section 6)
- QA/QC personnel (Sections 5, 7)
- Management (Sections 8, 9)
- System administrators (Sections 10, 11, 12)
- All users (Sections 1-4, 13)

**Prerequisites:**
- Basic computer literacy
- Understanding of pharmaceutical production processes
- Role-specific training completed

**Related Documents:**
- `ADMIN_GUIDE_PERMISSIONS_SECURITY.md` - Technical permission system details
- `USER_PASSWORDS.md` - Default user credentials
- `OPERATOR_ROLES.md` - Role definitions
- `SYSTEM_OVERVIEW.md` - High-level system architecture

**Revision History:**
- v1.0 (Dec 3, 2025): Initial comprehensive guide created

**Document Status:** ✅ Complete - Ready for User Training

**Screenshot Placeholders:** 60+ locations marked for future screenshot insertion

**Next Steps:**
1. Capture all screenshots (English interface)
2. Generate PDF version
3. Conduct user training sessions
4. Gather feedback and update

---

## 📧 FEEDBACK & SUPPORT

For questions about this guide or system functionality:

**Email:** training@kampalapharma.com

**Phone:** +256-XXX-XXXX

**In-Person:** Visit IT Support Office

**System Issues:** Submit ticket via admin portal or email it@kampalapharma.com

---

**© 2025 Kampala Pharmaceutical Industries - Operations System**
**All Rights Reserved - Internal Use Only**

---

*End of User Guide*

