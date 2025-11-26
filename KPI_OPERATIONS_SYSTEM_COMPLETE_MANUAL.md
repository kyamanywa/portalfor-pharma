# 📚 **KPI OPERATIONS SYSTEM - COMPLETE TECHNICAL MANUAL**
## Kampala Pharmaceutical Industries Operations Management System
### **Professional Edition - Customer Documentation**

---

## 📋 **TABLE OF CONTENTS**

1. [System Overview](#1-system-overview)
2. [Technical Specifications](#2-technical-specifications)
3. [User Management & Authentication](#3-user-management--authentication)
4. [Product Management](#4-product-management)
5. [Machine & Equipment Management](#5-machine--equipment-management)
6. [Workflow & Production Processes](#6-workflow--production-processes)
7. [BMR Creation & Management](#7-bmr-creation--management)
8. [Quality Control & Quarantine](#8-quality-control--quarantine)
9. [Analytics & Reporting](#9-analytics--reporting)
10. [System Configuration](#10-system-configuration)
11. [Alerts & Notifications](#11-alerts--notifications)
12. [Integration Capabilities](#12-integration-capabilities)
13. [System Capacity & Performance](#13-system-capacity--performance)
14. [Best Practices](#14-best-practices)
15. [Troubleshooting](#15-troubleshooting)

---

## **1. SYSTEM OVERVIEW**

### **1.1 What is the KPI Operations System?**

The KPI Operations System is a comprehensive pharmaceutical manufacturing management platform designed specifically for Good Manufacturing Practice (GMP) compliance. It manages the complete production lifecycle from raw materials to finished goods distribution.

**Core Capabilities:**
- ✅ Complete BMR (Batch Manufacturing Record) lifecycle management
- ✅ Real-time production workflow tracking
- ✅ Quality control integration with quarantine management
- ✅ Electronic signatures and audit trails
- ✅ Machine and equipment monitoring
- ✅ Inventory management (raw materials to finished goods)
- ✅ Advanced analytics and reporting
- ✅ Role-based access control (24 user roles)
- ✅ Regulatory compliance features

### **1.2 System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Raw Materials │───▶│   Production    │───▶│ Finished Goods  │
│   Management    │    │   Workflow      │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Quality Control │    │ Machine Tracking│    │ Sales & Distrib │
│ & Quarantine    │    │ & Performance   │    │ Management      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **1.3 Supported Product Types**

#### **Ointments**
- **Workflow**: Mixing → Tube Filling → Packaging → Quality Control → Storage
- **Key Features**: Temperature monitoring, viscosity tracking, tube fill accuracy

#### **Tablets (Normal)**
- **Workflow**: Granulation → Blending → Compression → [Coating] → Blister Packing → Storage
- **Key Features**: Weight uniformity, hardness testing, dissolution tracking

#### **Tablets (Type 2)**
- **Workflow**: Granulation → Blending → Compression → [Coating] → Bulk Packing → Storage
- **Key Features**: Same as normal tablets but with bulk packaging instead of blister

#### **Capsules**
- **Workflow**: Drying → Blending → Filling → Blister Packing → Storage
- **Key Features**: Fill weight accuracy, capsule integrity, dissolution testing

---

## **2. TECHNICAL SPECIFICATIONS**

### **2.1 System Requirements**

**Server Requirements:**
- **Operating System**: Windows 10/11, Windows Server 2019+, Linux (Ubuntu 20.04+)
- **Python**: Version 3.8 or higher
- **Database**: SQLite (development), PostgreSQL/MySQL (production)
- **Memory**: Minimum 4GB RAM, Recommended 8GB+
- **Storage**: Minimum 10GB available space
- **Network**: TCP/IP network connectivity

**Client Requirements:**
- **Web Browser**: Chrome 90+, Firefox 88+, Edge 90+
- **Internet Connection**: Required for system access
- **Resolution**: Minimum 1024x768, Recommended 1920x1080

### **2.2 Technology Stack**

```python
# Core Framework
Django 4.2.7                    # Web framework
Django REST Framework 3.14.0    # API framework
SQLite/PostgreSQL              # Database

# Frontend Technologies
Bootstrap 5.x                   # UI Framework
JavaScript (ES6+)              # Client-side scripting
Chart.js                       # Analytics visualization
jQuery 3.x                     # DOM manipulation

# Security & Authentication
Django OTP 1.2.2               # Two-factor authentication
CSRF Protection                # Cross-site request forgery protection
Session Management             # Secure session handling

# Additional Libraries
Pillow 10.0.1                  # Image processing
openpyxl 3.1.2                # Excel export functionality
django-filter 23.3            # Advanced filtering
channels 4.0.0                 # WebSocket support
```

### **2.3 Performance Metrics**

**Concurrent Users:**
- **Light Usage**: Up to 50 concurrent users
- **Moderate Usage**: Up to 100 concurrent users
- **Heavy Usage**: Up to 200 concurrent users (with proper server specs)

**Response Times:**
- **Dashboard Loading**: < 2 seconds
- **BMR Creation**: < 3 seconds
- **Report Generation**: < 5 seconds
- **Phase Updates**: < 1 second

**Data Capacity:**
- **BMR Records**: Unlimited (database dependent)
- **Phase Executions**: Up to 1 million+ records
- **User Accounts**: Up to 1,000 users
- **File Storage**: Limited by available disk space

---

## **3. USER MANAGEMENT & AUTHENTICATION**

### **3.1 User Roles & Permissions**

The system supports **24 distinct user roles** with granular permissions:

#### **Administrative Roles**
1. **Admin** (`admin`)
   - Complete system access
   - User management
   - System configuration
   - All dashboard access

2. **QA (Quality Assurance)** (`qa`)
   - BMR creation and management
   - Quality reviews and approvals
   - Final batch certification
   - QA dashboard access

3. **Regulatory** (`regulatory`)
   - Regulatory approvals
   - Compliance oversight
   - Documentation reviews
   - Regulatory dashboard

#### **Management Roles**
4. **Production Manager** (`production_manager`)
   - Production planning
   - BMR requests to QA
   - Resource allocation
   - Production dashboard

5. **Store Manager** (`store_manager`)
   - Raw material management
   - Inventory control
   - Material releases
   - Inventory dashboard

6. **Dispensing Manager** (`dispensing_manager`)
   - Material dispensing
   - Batch preparation
   - Dispensing records
   - Dispensing dashboard

#### **Quality & Control Roles**
7. **QC (Quality Control)** (`qc`)
   - Testing and analysis
   - Sample approvals/rejections
   - Test result recording
   - QC dashboard

8. **Quarantine Manager** (`quarantine`)
   - Quarantine management
   - Sample requests
   - Batch isolation control
   - Quarantine dashboard

#### **Storage Roles**
9. **Packaging Store** (`packaging_store`)
   - Packaging material management
   - Material releases for packing
   - Packaging inventory

10. **Finished Goods Store** (`finished_goods_store`)
    - Final product storage
    - Distribution management
    - Sales order fulfillment

#### **Production Operators (14 Roles)**
11. **Mixing Operator** (`mixing_operator`)
12. **Tube Filling Operator** (`tube_filling_operator`)
13. **Granulation Operator** (`granulation_operator`)
14. **Blending Operator** (`blending_operator`)
15. **Compression Operator** (`compression_operator`)
16. **Coating Operator** (`coating_operator`)
17. **Drying Operator** (`drying_operator`)
18. **Filling Operator** (`filling_operator`)
19. **Sorting Operator** (`sorting_operator`)
20. **Packing Operator** (`packing_operator`)
21. **Dispensing Operator** (`dispensing_operator`)
22. **Equipment Operator** (`equipment_operator`)
23. **Cleaning Operator** (`cleaning_operator`)

### **3.2 Authentication System**

**Login Process:**
```
1. Navigate to: http://[server-ip]:8000/accounts/login/
2. Enter username and password
3. System validates credentials
4. Automatic redirection to role-specific dashboard
5. Session established with timeout protection
```

**Security Features:**
- ✅ Secure password hashing (PBKDF2)
- ✅ Session timeout (configurable, default 30 minutes)
- ✅ CSRF protection
- ✅ Login attempt monitoring
- ✅ Audit trail logging
- ✅ Role-based access control
- ✅ Electronic signature capability

**Default Credentials (Change in Production):**
```
Admin: username=admin, password=admin123
QA: username=qa_user, password=qa123
Production Manager: username=production_manager, password=prod123
[Additional credentials in OPERATOR_ROLES.md]
```

---

## **4. PRODUCT MANAGEMENT**

### **4.1 Product Master Data**

The system manages comprehensive product information for three main product types:

#### **Product Model Structure**
```python
Product {
    product_name: "Product Name"
    product_type: "ointment|tablet|capsule"
    
    # Tablet-specific fields
    coating_type: "coated|uncoated"
    tablet_type: "normal|tablet_2"
    
    # Batch configuration
    standard_batch_size: 1000.00
    batch_size_unit: "tablets|capsules|tubes"
    packaging_size_in_units: 10.00
    
    # System fields
    is_active: true
    created_at: timestamp
    updated_at: timestamp
}
```

#### **4.2 Product Configuration**

**Ointment Configuration:**
- Batch size in tubes
- Tube fill volume
- Viscosity specifications
- Packaging requirements

**Tablet Configuration:**
- Coating options (Coated/Uncoated)
- Tablet type (Normal/Type 2)
- Weight specifications
- Hardness requirements
- Packaging type (Blister/Bulk)

**Capsule Configuration:**
- Capsule size specifications
- Fill weight requirements
- Dissolution parameters
- Packaging specifications

### **4.3 Ingredient Management**

**ProductIngredient Model:**
```python
Ingredient {
    product: Foreign Key to Product
    ingredient_name: "API Name"
    ingredient_type: "active|inactive|excipient"
    quantity_per_unit: 250.00
    unit_of_measure: "mg|g|ml|%"
    supplier: "Supplier Name"
}
```

**Quality Specifications:**
```python
ProductSpecification {
    product: Foreign Key to Product
    parameter_name: "Assay"
    specification: "90.0-110.0%"
    test_method: "HPLC"
    acceptance_criteria: "95.0-105.0%"
}
```

---

## **5. MACHINE & EQUIPMENT MANAGEMENT**

### **5.1 Machine Types Supported**

The system tracks **6 machine categories**:

1. **Granulation Machines**
   - Wet granulation equipment
   - Dry granulation rollers
   - Fluid bed granulators

2. **Blending Machines**
   - V-blenders
   - Ribbon blenders
   - Tumble blenders

3. **Compression Machines**
   - Single punch tablets
   - Multi-station tablet presses
   - High-speed compression

4. **Coating Machines**
   - Fluid bed coaters
   - Pan coating systems
   - Spray coating equipment

5. **Blister Packing Machines**
   - Thermoforming lines
   - Cold forming equipment
   - Strip packing machines

6. **Filling Machines**
   - Capsule filling equipment
   - Tube filling machines
   - Bottle filling systems

### **5.2 Machine Tracking Features**

**Performance Monitoring:**
```python
BatchPhaseExecution {
    machine_used: Foreign Key to Machine
    
    # Breakdown tracking
    breakdown_occurred: boolean
    breakdown_start_time: timestamp
    breakdown_end_time: timestamp
    breakdown_reason: text
    breakdown_duration: calculated (minutes)
    
    # Changeover tracking
    changeover_occurred: boolean
    changeover_start_time: timestamp
    changeover_end_time: timestamp
    changeover_reason: text
    changeover_duration: calculated (minutes)
}
```

**Machine Utilization Analytics:**
- Runtime hours per machine
- Breakdown frequency and duration
- Changeover time analysis
- Efficiency calculations
- Maintenance scheduling integration

### **5.3 Equipment Status Management**

**Machine States:**
- ✅ **Active**: Available for production
- ⚠️ **Maintenance**: Scheduled maintenance
- ❌ **Breakdown**: Equipment failure
- 🔄 **Changeover**: Product changeover in progress
- 📊 **Performance Review**: Efficiency analysis

---

## **6. WORKFLOW & PRODUCTION PROCESSES**

### **6.1 Workflow Templates**

The system uses **dynamic workflow templates** that automatically adapt based on product configuration:

#### **Ointment Workflow**
```
1. BMR Creation
2. Regulatory Approval
3. Material Dispensing
4. Mixing (Machine Required)
5. Post-Mixing QC
6. Tube Filling (Machine Required)
7. Quality Control
8. Packaging Material Release
9. Secondary Packaging
10. Final QA
11. Finished Goods Store
```

#### **Tablet Workflow (Normal)**
```
1. BMR Creation
2. Regulatory Approval
3. Material Dispensing
4. Granulation (Machine Required)
5. Post-Granulation QC
6. Blending (Machine Required)
7. Post-Blending QC
8. Compression (Machine Required)
9. Post-Compression QC
10. Coating (Conditional - if product.is_coated)
11. Sorting
12. Quality Control
13. Blister Packing (Machine Required)
14. Packaging Material Release
15. Secondary Packaging
16. Final QA
17. Finished Goods Store
```

#### **Tablet Workflow (Type 2)**
```
[Same as Normal Tablet until step 12]
13. Bulk Packing (instead of Blister)
[Continue with steps 14-17]
```

#### **Capsule Workflow**
```
1. BMR Creation
2. Regulatory Approval
3. Material Dispensing
4. Drying (Machine Required)
5. Blending (Machine Required)
6. Post-Blending QC
7. Filling (Machine Required)
8. Quality Control
9. Blister Packing (Machine Required)
10. Packaging Material Release
11. Secondary Packaging
12. Final QA
13. Finished Goods Store
```

### **6.2 Phase Execution Tracking**

**Phase Status Lifecycle:**
```
not_ready → pending → in_progress → completed
                  ↓
              failed → rolled_back
                  ↓
               skipped
```

**Phase Execution Data:**
```python
BatchPhaseExecution {
    bmr: BMR reference
    phase: ProductionPhase reference
    status: Phase status
    
    # Personnel tracking
    started_by: User who started the phase
    completed_by: User who completed the phase
    
    # Timing
    created_date: Phase creation time
    started_date: Phase start time
    completed_date: Phase completion time
    duration_hours: Calculated duration
    
    # Quality control
    qc_approved: QC approval status
    qc_approved_by: QC approver
    qc_approval_date: QC approval timestamp
    rejection_reason: Failure reason if rejected
    
    # Flexible data storage
    phase_data: JSON field for phase-specific data
    operator_comments: Operator notes
    qa_comments: QA review comments
}
```

### **6.3 Automatic Phase Progression**

**Intelligence Features:**
- ✅ **Smart Phase Routing**: Automatically determines next phase based on product type
- ✅ **Conditional Phases**: Skips coating for uncoated tablets
- ✅ **Quality Gates**: Enforces QC checkpoints
- ✅ **Rollback Capability**: Returns to previous phase on QC failure
- ✅ **Parallel Processing**: Multiple batches can progress simultaneously

---

## **7. BMR CREATION & MANAGEMENT**

### **7.1 BMR Lifecycle**

**BMR Status Progression:**
```
Draft → Submitted → Approved → In Production → Completed
  ↓         ↓          ↓
Cancelled  Rejected   [Can return to previous steps]
```

### **7.2 BMR Creation Process**

**Step 1: Production Manager Request**
```python
BMRRequest {
    requested_by: Production Manager
    product: Product selection
    requested_quantity: Batch size
    planned_start_date: Production schedule
    urgency_level: "normal|urgent|critical"
    justification: Business reason
    status: "pending|approved|rejected"
}
```

**Step 2: QA BMR Creation**
```python
BMR {
    bmr_number: Auto-generated unique ID
    batch_number: Manual entry (XXXYYYY format)
    manufacturing_date: Production date
    product: Product reference
    
    # Batch specifications
    actual_batch_size: Actual production quantity
    actual_batch_size_unit: Unit of measure
    
    # Planning dates
    planned_start_date: Scheduled start
    planned_completion_date: Scheduled end
    actual_start_date: Real start time
    actual_completion_date: Real completion time
    
    # Approval workflow
    created_by: QA user
    approved_by: Regulatory user
    approved_date: Approval timestamp
    
    # Documentation
    manufacturing_instructions: Detailed procedures
    special_instructions: Special handling notes
    in_process_controls: Quality checkpoints
    quality_checks_required: Testing requirements
    
    # Review comments
    qa_comments: QA notes
    regulatory_comments: Regulatory feedback
}
```

**Step 3: Material Requirements**
```python
BMRMaterial {
    bmr: BMR reference
    material_name: Raw material
    required_quantity: Amount needed
    unit_of_measure: kg, L, units
    specification: Quality specs
    supplier: Approved supplier
    lot_number: Material lot
    expiry_date: Material expiry
    dispensed_by: Dispensing user
    dispensed_date: Dispensing time
    actual_quantity: Actually dispensed
}
```

### **7.3 Electronic Signatures**

**Digital Approval Process:**
```python
BMRSignature {
    bmr: BMR reference
    signature_type: "creation|approval|completion"
    signed_by: User who signed
    signature_date: Signing timestamp
    signature_meaning: "Created by|Approved by|Completed by"
    signature_reason: Approval reason
    electronic_signature: Digital signature data
}
```

**Signature Requirements:**
- ✅ BMR Creation: QA signature required
- ✅ Regulatory Approval: Regulatory signature required
- ✅ Production Completion: QA final signature required
- ✅ Quality Release: QC signature required

### **7.4 Batch Number Validation**

**Format Requirements:**
```
Pattern: XXXYYYY
X = Batch sequence (001, 002, 003...)
Y = Year (2025, 2026...)

Examples:
- 0012025 = 1st batch of 2025
- 0022025 = 2nd batch of 2025
- 1502024 = 150th batch of 2024
```

**Validation Rules:**
- ✅ Must be exactly 7 characters
- ✅ First 3 characters: numeric sequence
- ✅ Last 4 characters: year
- ✅ Must be unique across all BMRs
- ✅ Manual entry required (no auto-generation)

---

## **8. QUALITY CONTROL & QUARANTINE**

### **8.1 Quarantine Management**

**Quarantine Workflow:**
```
Production Phase Complete → Quarantine → Sample Request → 
QA Sampling → QC Testing → Approval/Rejection → 
Release to Next Phase OR Return to Previous Phase
```

**QuarantineBatch Model:**
```python
QuarantineBatch {
    bmr: BMR reference
    current_phase: Phase where quarantine occurred
    status: "quarantined|sample_requested|sample_in_qa|
             sample_in_qc|sample_approved|sample_failed|released"
    quarantine_date: When quarantine started
    released_date: When released from quarantine
    released_by: User who authorized release
    sample_count: Number of samples requested (max 2)
    quarantine_duration_hours: Time in quarantine
}
```

### **8.2 Sample Request System**

**Sample Management:**
```python
SampleRequest {
    quarantine_batch: Quarantine reference
    sample_number: 1 or 2 (max 2 samples per quarantine)
    
    # Request stage
    requested_by: Quarantine manager
    request_date: Sample request time
    
    # QA sampling stage
    sampled_by: QA personnel
    sample_date: When sample was taken
    qa_comments: QA observations
    
    # QC testing stage
    received_by: QC analyst
    received_date: When QC received sample
    test_results: Testing data (JSON)
    qc_status: "pending|approved|failed"
    qc_comments: QC findings
    approved_date: Final approval/rejection date
}
```

### **8.3 Quality Control Integration**

**QC Checkpoints:**
- ✅ **Post-Mixing QC**: Raw material blend verification
- ✅ **Post-Granulation QC**: Granule quality assessment
- ✅ **Post-Blending QC**: Final blend uniformity
- ✅ **Post-Compression QC**: Tablet quality testing
- ✅ **Quality Control**: Final product testing
- ✅ **Final QA**: Release approval

**QC Test Parameters:**
- Weight uniformity
- Content uniformity
- Dissolution testing
- Hardness testing
- Friability testing
- Disintegration testing
- Assay determination
- Impurity testing

### **8.4 Quarantine Rules**

**Automatic Quarantine Triggers:**
- ✅ QC test failures
- ✅ Process deviations
- ✅ Equipment malfunctions during production
- ✅ Environmental excursions
- ✅ Manual quarantine requests

**Quarantine Resolution:**
- ✅ **Sample Approved**: Batch continues to next phase
- ✅ **Sample Failed**: Batch returns to previous corrective phase
- ✅ **Investigation Required**: Extended quarantine with investigation
- ✅ **Batch Rejection**: Complete batch disposal

---

## **9. ANALYTICS & REPORTING**

### **9.1 Production Analytics**

**Real-Time Dashboards:**
- 📊 **Production Overview**: Active batches, phase status, completion rates
- 📈 **Performance Metrics**: Cycle times, efficiency, throughput
- 🎯 **Quality Indicators**: Pass rates, rejection rates, quarantine frequency
- ⚡ **Machine Utilization**: Runtime, breakdowns, changeover times

**Key Performance Indicators (KPIs):**
```python
Production KPIs {
    # Efficiency Metrics
    overall_equipment_efficiency: percentage
    cycle_time_variance: hours
    throughput_rate: batches/day
    
    # Quality Metrics
    first_pass_yield: percentage
    quality_cost_ratio: percentage
    customer_complaints: count
    
    # Operational Metrics
    machine_downtime: hours
    changeover_time: minutes
    inventory_turnover: ratio
    
    # Compliance Metrics
    regulatory_deviations: count
    audit_findings: count
    batch_rejections: percentage
}
```

### **9.2 Timeline Visualization**

**Gantt Chart Features:**
- ✅ **Production Timeline**: Visual representation of all active BMRs
- ✅ **Phase Progress**: Real-time phase completion status
- ✅ **Critical Path**: Identification of bottlenecks and delays
- ✅ **Resource Allocation**: Machine and personnel utilization
- ✅ **Milestone Tracking**: Key production milestones

**Timeline Analytics:**
```python
Timeline Metrics {
    planned_vs_actual: duration comparison
    phase_bottlenecks: slowest phases identification
    resource_conflicts: scheduling conflicts
    delay_root_causes: analysis of delays
    capacity_utilization: resource usage efficiency
}
```

### **9.3 Export Capabilities**

**Report Formats:**
- 📊 **Excel Export**: Detailed data with charts and pivot tables
- 📄 **PDF Reports**: Professional formatted reports
- 📋 **CSV Data**: Raw data for external analysis
- 🔗 **API Access**: Real-time data integration

**Available Reports:**
1. **Production Summary Report**: Overall production statistics
2. **Quality Control Report**: QC test results and trends
3. **Machine Utilization Report**: Equipment performance analysis
4. **Batch History Report**: Complete batch lifecycle tracking
5. **Compliance Audit Report**: Regulatory compliance documentation
6. **Cost Analysis Report**: Production cost breakdowns
7. **Performance Dashboard**: Executive KPI summary

### **9.4 Advanced Analytics**

**Predictive Analytics Features:**
- 🔮 **Production Forecasting**: Capacity planning and demand prediction
- 📊 **Quality Trend Analysis**: Identification of quality patterns
- ⚡ **Equipment Maintenance**: Predictive maintenance scheduling
- 📈 **Process Optimization**: Continuous improvement recommendations

**Machine Learning Integration:**
```python
Analytics Engine {
    # Time series analysis
    production_forecasting: ARIMA models
    
    # Quality prediction
    defect_prediction: Classification algorithms
    
    # Optimization
    schedule_optimization: Genetic algorithms
    resource_optimization: Linear programming
    
    # Anomaly detection
    process_deviation_detection: Statistical models
    equipment_failure_prediction: Survival analysis
}
```

---

## **10. SYSTEM CONFIGURATION**

### **10.1 Admin Settings Management**

The system provides **62 configurable parameters** across 4 categories:

#### **Dashboard Settings (17 Parameters)**
```python
DashboardSettings {
    # Performance
    page_size: 25                    # Items per page
    refresh_interval: 30             # Auto-refresh seconds
    chart_animation: true            # Enable animations
    
    # Display
    show_progress_bars: true         # Phase progress display
    show_phase_durations: true       # Duration visibility
    compact_view: false              # Layout mode
    
    # Functionality
    enable_quick_actions: true       # Quick action buttons
    show_machine_status: true        # Machine status indicators
    enable_bulk_operations: true     # Bulk actions
    auto_save_drafts: true          # Auto-save feature
    
    # Notifications
    show_realtime_updates: true      # Live updates
    enable_sound_alerts: false       # Audio notifications
    popup_notifications: true       # Browser popups
    
    # Advanced
    enable_advanced_filters: true   # Complex filtering
    show_analytics_widgets: true    # Dashboard widgets
    cache_dashboard_data: true      # Performance caching
    export_batch_limit: 1000       # Export limitations
}
```

#### **System Alert Settings (15 Parameters)**
```python
SystemAlertSettings {
    # Alert Timing
    phase_warning_threshold: 80     # Warning at 80% of expected time
    phase_overrun_threshold: 120    # Critical at 120% of expected time
    batch_delay_threshold: 24       # Batch delay warning (hours)
    
    # Machine Alerts
    breakdown_alert_enabled: true   # Machine breakdown alerts
    maintenance_reminder_days: 7    # Maintenance reminders
    utilization_warning_threshold: 90  # High utilization warning
    
    # Quality Alerts
    qc_failure_alert_enabled: true  # QC failure notifications
    quarantine_alert_enabled: true  # Quarantine notifications
    deviation_alert_enabled: true   # Process deviation alerts
    
    # Inventory Alerts
    low_stock_threshold: 10         # Low stock warning
    expiry_warning_days: 30         # Material expiry warning
    
    # System Alerts
    system_performance_monitoring: true  # Performance alerts
    database_backup_alerts: true    # Backup status alerts
    security_alert_enabled: true    # Security notifications
    error_notification_enabled: true # System error alerts
}
```

#### **Session Management Settings (15 Parameters)**
```python
SessionManagementSettings {
    # Session Security
    session_timeout_minutes: 30     # Inactive session timeout
    max_concurrent_sessions: 3      # Max sessions per user
    force_logout_on_timeout: true   # Forced logout
    
    # Password Security
    password_expiry_days: 90        # Password expiration
    min_password_length: 8          # Minimum password length
    require_password_complexity: true  # Complex passwords
    
    # Login Security
    max_failed_attempts: 3          # Account lockout threshold
    lockout_duration_minutes: 15    # Lockout duration
    require_2fa_admin: false        # Two-factor authentication
    
    # Audit & Compliance
    log_user_actions: true          # Action logging
    audit_trail_retention_days: 365 # Log retention
    
    # Session Management
    remember_login_days: 7          # Remember me duration
    idle_warning_minutes: 25        # Idle warning time
    auto_save_interval_seconds: 300  # Auto-save frequency
    cleanup_expired_sessions: true  # Session cleanup
}
```

#### **Production Limits Settings (15 Parameters)**
```python
ProductionLimitsSettings {
    # Capacity Limits
    max_concurrent_batches: 50      # Maximum active batches
    max_batch_size: 100000         # Maximum batch size
    max_daily_production: 10        # Daily batch limit
    
    # Quality Limits
    max_qc_samples_per_batch: 2    # Sample limit per batch
    max_quarantine_duration_hours: 168  # Max quarantine time
    quality_hold_time_hours: 72    # Quality hold duration
    
    # Performance Limits
    max_phase_duration_hours: 48   # Maximum phase duration
    breakdown_tolerance_minutes: 120  # Breakdown tolerance
    changeover_time_limit_minutes: 60  # Changeover time limit
    
    # Resource Limits
    max_operators_per_phase: 3     # Operator limit per phase
    max_machine_utilization: 95    # Maximum utilization %
    
    # Data Limits
    max_export_records: 10000      # Export record limit
    max_report_range_days: 90      # Report date range limit
    max_file_upload_size_mb: 10    # File upload limit
    database_cleanup_days: 1095    # Data retention period
}
```

### **10.2 Configuration Management**

**Admin Interface Access:**
```
URL: http://[server]:8000/admin/workflow/
Sections:
- Dashboard Settings
- System Alert Settings  
- Session Management Settings
- Production Limits Settings
```

**Configuration Features:**
- ✅ **Hot Configuration**: Changes apply immediately (no restart required)
- ✅ **Type Safety**: Automatic type conversion and validation
- ✅ **Default Values**: Sensible defaults for all settings
- ✅ **Bulk Actions**: Reset to defaults, export/import settings
- ✅ **Audit Trail**: All configuration changes logged
- ✅ **Template Access**: Settings available in all templates

### **10.3 System Maintenance**

**Automated Maintenance:**
```python
Management Commands {
    # Database maintenance
    python manage.py cleanup_expired_sessions
    python manage.py vacuum_database
    python manage.py backup_database
    
    # Data initialization
    python manage.py init_admin_settings
    python manage.py init_system_defaults
    python manage.py create_sample_data
    
    # Performance optimization
    python manage.py optimize_database
    python manage.py clear_cache
    python manage.py generate_reports
}
```

**Backup Procedures:**
- 🔄 **Automatic Backups**: Daily database backups
- 💾 **Manual Backups**: On-demand backup creation
- 📤 **Export Functions**: Data export for migration
- 🔐 **Secure Storage**: Encrypted backup storage

---

## **11. ALERTS & NOTIFICATIONS**

### **11.1 Alert System Architecture**

**Alert Categories:**
1. **Production Alerts**: Phase delays, batch issues
2. **Quality Alerts**: QC failures, deviations
3. **Machine Alerts**: Breakdowns, maintenance
4. **Inventory Alerts**: Stock levels, expiry
5. **System Alerts**: Performance, security

### **11.2 Notification Channels**

**Built-in Notifications:**
- 🔔 **Dashboard Alerts**: Real-time dashboard notifications
- 📧 **Email Notifications**: Automated email alerts (configurable)
- 🌐 **Web Notifications**: Browser push notifications
- 📱 **Mobile Alerts**: Mobile-responsive notifications

**Alert Delivery:**
```python
NotificationSystem {
    # Immediate alerts
    critical_alerts: real_time_delivery
    
    # Batched alerts  
    warning_alerts: 15_minute_batches
    
    # Daily summaries
    info_alerts: daily_digest
    
    # Emergency alerts
    emergency_alerts: immediate_all_channels
}
```

### **11.3 Alert Configuration**

**Configurable Alert Types:**
```python
AlertConfiguration {
    # Production Alerts
    phase_delay_alert: {
        enabled: true,
        threshold_percentage: 80,
        recipients: ["production_manager", "qa"],
        channels: ["dashboard", "email"]
    },
    
    # Quality Alerts
    qc_failure_alert: {
        enabled: true,
        severity: "critical",
        recipients: ["qc", "qa", "admin"],
        channels: ["dashboard", "email", "sms"]
    },
    
    # Machine Alerts
    breakdown_alert: {
        enabled: true,
        threshold_minutes: 5,
        recipients: ["equipment_operator", "production_manager"],
        channels: ["dashboard", "email"]
    }
}
```

### **11.4 Alert Escalation**

**Escalation Matrix:**
```
Level 1 (0-15 min): Direct operator notification
Level 2 (15-30 min): Supervisor notification
Level 3 (30-60 min): Manager notification
Level 4 (60+ min): Administrative notification
```

---

## **12. INTEGRATION CAPABILITIES**

### **12.1 API Architecture**

**REST API Endpoints:**
```python
API_Endpoints {
    # Authentication
    POST /api/v1/auth/login/
    POST /api/v1/auth/logout/
    POST /api/v1/auth/refresh/
    
    # BMR Management
    GET    /api/v1/bmr/
    POST   /api/v1/bmr/
    GET    /api/v1/bmr/{id}/
    PUT    /api/v1/bmr/{id}/
    DELETE /api/v1/bmr/{id}/
    
    # Production Workflow
    GET  /api/v1/workflow/phases/
    POST /api/v1/workflow/execute/
    PUT  /api/v1/workflow/complete/
    
    # Quality Control
    GET  /api/v1/qc/samples/
    POST /api/v1/qc/approve/
    POST /api/v1/qc/reject/
    
    # Analytics & Reporting
    GET /api/v1/analytics/production/
    GET /api/v1/analytics/quality/
    GET /api/v1/reports/export/
    
    # System Configuration
    GET /api/v1/config/settings/
    PUT /api/v1/config/settings/
}
```

**API Authentication:**
```python
Authentication Methods {
    # Token-based authentication
    token_auth: "Bearer <token>"
    
    # Session authentication  
    session_auth: "Django session cookies"
    
    # API Key authentication
    api_key_auth: "X-API-Key: <key>"
}
```

### **12.2 External System Integration**

**ERP Integration:**
```python
ERP_Integration {
    # Financial data
    cost_accounting: "Material costs, labor costs"
    inventory_valuation: "Stock valuations"
    
    # Procurement
    purchase_orders: "Raw material orders"
    vendor_management: "Supplier information"
    
    # Sales & Distribution
    sales_orders: "Customer orders"
    shipment_tracking: "Delivery information"
}
```

**LIMS Integration:**
```python
LIMS_Integration {
    # Sample management
    sample_registration: "Automatic sample creation"
    test_results: "Automated result import"
    
    # Quality data
    certificate_generation: "Quality certificates"
    trend_analysis: "Quality trending"
    
    # Compliance
    regulatory_reporting: "Automated compliance reports"
    audit_trails: "Complete audit documentation"
}
```

**MES Integration:**
```python
MES_Integration {
    # Equipment data
    machine_data: "Real-time equipment status"
    process_parameters: "Live process data"
    
    # Production execution
    work_instructions: "Digital work instructions"
    operator_guidance: "Step-by-step guidance"
    
    # Performance monitoring
    oee_calculation: "Overall Equipment Effectiveness"
    performance_metrics: "Real-time KPIs"
}
```

### **12.3 Data Exchange Formats**

**Supported Formats:**
- 📊 **JSON**: Primary API format
- 📄 **XML**: Legacy system integration
- 📋 **CSV**: Data import/export
- 📈 **Excel**: Report generation
- 🔗 **HL7**: Healthcare data exchange
- 📡 **OPC-UA**: Industrial automation

### **12.4 Webhook Support**

**Event-Driven Integration:**
```python
Webhook_Events {
    # Production events
    "bmr.created": "New BMR created",
    "phase.started": "Production phase started",
    "phase.completed": "Production phase completed",
    
    # Quality events
    "qc.failed": "Quality control failure",
    "batch.quarantined": "Batch quarantined",
    "batch.approved": "Batch approved for release",
    
    # System events
    "system.alert": "System alert triggered",
    "user.login": "User authentication event",
    "config.changed": "Configuration modified"
}
```

---

## **13. SYSTEM CAPACITY & PERFORMANCE**

### **13.1 Scalability Specifications**

**User Capacity:**
```python
User_Limits {
    # Concurrent users
    light_usage: 50,      # Basic operations
    moderate_usage: 100,  # Normal operations  
    heavy_usage: 200,     # Peak operations
    
    # Total registered users
    max_users: 1000,
    
    # Simultaneous sessions
    max_sessions_per_user: 3,
    max_total_sessions: 300
}
```

**Data Capacity:**
```python
Data_Limits {
    # Core entities
    max_bmr_records: "Unlimited*",
    max_phase_executions: "1M+ records",
    max_products: 10000,
    max_machines: 500,
    
    # Performance thresholds
    bmr_query_response_time: "< 2 seconds",
    dashboard_load_time: "< 3 seconds",
    report_generation_time: "< 10 seconds",
    
    # Storage requirements  
    database_size_estimate: "100MB per 1000 BMRs",
    log_retention: "1 year default",
    backup_storage: "3x database size"
}
```

### **13.2 Performance Optimization**

**Database Optimization:**
```python
Performance_Features {
    # Query optimization
    database_indexing: "Strategic indexes on frequently queried fields",
    query_caching: "Django query result caching",
    connection_pooling: "Database connection optimization",
    
    # Application optimization
    template_caching: "Template fragment caching",
    static_file_optimization: "CSS/JS minification and compression",
    image_optimization: "Automatic image compression",
    
    # Infrastructure optimization
    load_balancing: "Multiple server deployment support",
    cdn_integration: "Content delivery network support",
    redis_caching: "In-memory caching for session data"
}
```

### **13.3 System Monitoring**

**Performance Metrics:**
```python
Monitoring_KPIs {
    # Response times
    avg_response_time: "< 2 seconds",
    p95_response_time: "< 5 seconds",
    p99_response_time: "< 10 seconds",
    
    # Resource utilization
    cpu_utilization: "< 80%",
    memory_utilization: "< 85%",
    disk_utilization: "< 90%",
    
    # Application metrics
    database_query_time: "< 1 second average",
    error_rate: "< 0.1%",
    uptime: "> 99.5%"
}
```

**Health Check Endpoints:**
```python
Health_Checks {
    # System health
    GET /api/v1/health/: "Overall system status",
    GET /api/v1/health/database/: "Database connectivity",
    GET /api/v1/health/cache/: "Cache system status",
    
    # Performance metrics
    GET /api/v1/metrics/performance/: "Performance statistics",
    GET /api/v1/metrics/usage/: "Usage statistics",
    GET /api/v1/metrics/errors/: "Error tracking"
}
```

### **13.4 Deployment Architecture**

**Single Server Deployment:**
```
Application Server (Django) + Database (SQLite/PostgreSQL)
Recommended for: 1-50 users
Hardware: 4GB RAM, 2 CPU cores, 100GB storage
```

**Multi-Server Deployment:**
```
Load Balancer → Application Servers (N) → Database Cluster
Recommended for: 50+ users
Hardware: 8GB+ RAM per server, 4+ CPU cores, 500GB+ storage
```

**Cloud Deployment:**
```python
Cloud_Options {
    # Platform-as-a-Service
    heroku: "Simplified deployment and scaling",
    aws_elastic_beanstalk: "AWS managed deployment",
    azure_app_service: "Microsoft Azure deployment",
    
    # Infrastructure-as-a-Service  
    aws_ec2: "Full control AWS deployment",
    azure_virtual_machines: "Azure VM deployment",
    google_compute_engine: "Google Cloud deployment",
    
    # Container deployment
    docker: "Containerized deployment",
    kubernetes: "Orchestrated container deployment"
}
```

---

## **14. BEST PRACTICES**

### **14.1 Security Best Practices**

**User Account Management:**
```python
Security_Guidelines {
    # Password management
    "Use strong, unique passwords (min 8 characters)",
    "Enable two-factor authentication for admin accounts",
    "Regular password rotation (90 days)",
    "No password sharing between users",
    
    # Access control
    "Assign minimum required permissions",
    "Regular access review and cleanup",
    "Immediate access revocation for terminated users",
    "Monitor suspicious login activities",
    
    # Data protection
    "Regular database backups",
    "Encryption for sensitive data",
    "Secure network communications (HTTPS)",
    "Regular security updates and patches"
}
```

### **14.2 Operational Best Practices**

**Production Workflow Management:**
```python
Workflow_Best_Practices {
    # BMR management
    "Complete all required fields before approval",
    "Verify batch numbers for uniqueness",
    "Maintain current material specifications",
    "Regular review of manufacturing instructions",
    
    # Phase execution
    "Start phases only when ready",
    "Complete accurate phase documentation", 
    "Report equipment issues immediately",
    "Follow proper changeover procedures",
    
    # Quality control
    "Timely QC sample processing",
    "Accurate test result recording",
    "Proper quarantine management",
    "Complete deviation investigations"
}
```

### **14.3 System Maintenance**

**Regular Maintenance Tasks:**
```python
Maintenance_Schedule {
    # Daily tasks
    "Monitor system performance",
    "Check error logs",
    "Verify backup completion",
    
    # Weekly tasks  
    "Review user activity logs",
    "Clean up temporary files",
    "Update system statistics",
    
    # Monthly tasks
    "Database performance optimization",
    "Security patch updates",
    "User access review",
    
    # Quarterly tasks
    "Full system backup verification",
    "Performance benchmark testing",
    "Security vulnerability assessment"
}
```

### **14.4 Data Management**

**Data Integrity Guidelines:**
```python
Data_Management {
    # Backup strategy
    "Daily automated backups",
    "Weekly full system backups", 
    "Monthly backup restoration testing",
    "Offsite backup storage",
    
    # Data validation
    "Regular data consistency checks",
    "Automated data validation rules",
    "Manual data verification procedures",
    "Error correction protocols",
    
    # Compliance
    "Maintain complete audit trails",
    "Regular compliance assessments",
    "Documentation version control",
    "Change control procedures"
}
```

### **14.5 Performance Optimization**

**System Performance:**
```python
Performance_Guidelines {
    # Database optimization
    "Regular database maintenance",
    "Index optimization",
    "Query performance monitoring",
    "Data archival procedures",
    
    # Application optimization
    "Regular cache cleanup",
    "Static file optimization",
    "Memory usage monitoring",
    "Connection pool optimization",
    
    # User experience
    "Monitor page load times", 
    "Optimize large data exports",
    "Implement progressive loading",
    "Regular user feedback collection"
}
```

---

## **15. TROUBLESHOOTING**

### **15.1 Common Issues & Solutions**

#### **Login Issues**

**Problem**: Cannot login to system
**Solutions:**
```
1. Verify username/password combination
2. Check caps lock and keyboard layout  
3. Clear browser cache and cookies
4. Try different browser
5. Contact administrator for password reset
6. Check if account is locked due to failed attempts
```

**Problem**: Session timeout too frequent  
**Solutions:**
```
1. Increase session timeout in admin settings
2. Enable "Remember Me" option
3. Check for browser security settings
4. Verify system clock synchronization
```

#### **Performance Issues**

**Problem**: Slow dashboard loading
**Solutions:**
```
1. Clear browser cache
2. Check network connection
3. Reduce dashboard data range
4. Enable data caching in admin settings
5. Contact administrator for server performance check
```

**Problem**: Export/report generation timeout
**Solutions:**
```
1. Reduce data range for export
2. Use smaller batch sizes
3. Schedule reports during off-peak hours
4. Contact administrator for timeout adjustment
```

#### **Data Issues**

**Problem**: BMR not appearing in workflow
**Solutions:**
```
1. Verify BMR approval status
2. Check workflow template configuration
3. Refresh browser page
4. Check user role permissions
5. Contact QA for BMR status verification
```

**Problem**: Phase cannot be started
**Solutions:**
```
1. Verify previous phase completion
2. Check user role permissions for phase
3. Ensure required materials are dispensed
4. Verify machine availability
5. Check for active quarantine holds
```

### **15.2 Error Code Reference**

**System Error Codes:**
```python
Error_Codes {
    # Authentication errors
    "AUTH_001": "Invalid credentials",
    "AUTH_002": "Account locked",
    "AUTH_003": "Session expired",
    "AUTH_004": "Insufficient permissions",
    
    # Workflow errors
    "WF_001": "Phase not ready for execution", 
    "WF_002": "Previous phase not completed",
    "WF_003": "Required machine not available",
    "WF_004": "Materials not dispensed",
    
    # Quality control errors
    "QC_001": "Sample already exists",
    "QC_002": "Maximum samples exceeded",
    "QC_003": "Batch not in quarantine",
    "QC_004": "QC test results pending",
    
    # System errors
    "SYS_001": "Database connection error",
    "SYS_002": "Configuration error",
    "SYS_003": "File upload error", 
    "SYS_004": "Report generation error"
}
```

### **15.3 Log File Locations**

**System Log Files:**
```
Application Logs: ./logs/django.log
Error Logs: ./logs/error.log
User Activity: ./logs/user_activity.log
Database Logs: ./logs/database.log
Performance Logs: ./logs/performance.log
Security Logs: ./logs/security.log
```

### **15.4 Emergency Procedures**

**System Recovery:**
```python
Emergency_Procedures {
    # Database corruption
    "1. Stop application server",
    "2. Restore from latest backup",
    "3. Verify data integrity",
    "4. Restart application",
    "5. Notify users of recovery",
    
    # Security breach
    "1. Immediately change all admin passwords",
    "2. Review user access logs",
    "3. Check for unauthorized changes",
    "4. Update security patches",
    "5. Implement additional security measures",
    
    # Performance degradation
    "1. Check server resource utilization",
    "2. Review database performance",
    "3. Clear system caches",
    "4. Restart application if necessary",
    "5. Monitor system recovery"
}
```

### **15.5 Support Contacts**

**Technical Support:**
```
System Administrator: admin@kampala-pharma.com
Database Support: db-admin@kampala-pharma.com  
Security Issues: security@kampala-pharma.com
User Training: training@kampala-pharma.com
24/7 Emergency: +256-XXX-XXXX
```

---

## **16. APPENDICES**

### **Appendix A: API Documentation**
[Complete API reference with examples]

### **Appendix B: Database Schema**
[Detailed database structure and relationships]

### **Appendix C: Configuration Files**
[Sample configuration files and settings]

### **Appendix D: Installation Guide**
[Step-by-step installation instructions]

### **Appendix E: Regulatory Compliance**
[GMP compliance features and documentation]

---

## **COPYRIGHT & LICENSING**

**© 2025 Kampala Pharmaceutical Industries**  
**KPI Operations System - Professional Edition**

This manual contains proprietary information and is intended solely for authorized users of the KPI Operations System. Unauthorized reproduction or distribution is prohibited.

**Software Version**: 2.0.0  
**Manual Version**: 1.0  
**Last Updated**: November 2025

---

**📧 For support and questions, contact: support@kampala-pharma.com**  
**🌐 Website: www.kampala-pharma.com**  
**📱 Phone: +256-XXX-XXXX**