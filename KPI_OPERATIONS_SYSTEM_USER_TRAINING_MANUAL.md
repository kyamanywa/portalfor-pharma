# 📚 KPI OPERATIONS SYSTEM - USER TRAINING MANUAL

## Kampala Pharmaceutical Industries
### Operations Management System - Complete User Guide

---

## 📋 TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Security & Authentication](#security--authentication)
3. [User Roles & Permissions](#user-roles--permissions)
4. [Getting Started](#getting-started)
5. [Dashboard Navigation](#dashboard-navigation)
6. [Core Workflows](#core-workflows)
7. [Data Input Requirements](#data-input-requirements)
8. [Production Process Management](#production-process-management)
9. [Quality Control Procedures](#quality-control-procedures)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## 🏭 SYSTEM OVERVIEW

### What is the KPI Operations System?

The KPI Operations System is a comprehensive pharmaceutical operations management platform that manages the complete production workflow from BMR (Batch Manufacturing Record) creation to finished goods storage.

### Key Features:
- ✅ **Complete Production Workflow Management**
- ✅ **Real-time Phase Tracking**
- ✅ **Quality Control Integration**
- ✅ **Material Management**
- ✅ **Audit Trail & Compliance**
- ✅ **Role-based Access Control**
- ✅ **Performance Analytics**

### System Architecture:
```
Raw Materials → Material Dispensing → Production Phases → Quality Control → Finished Goods
```

---

## 🔐 SECURITY & AUTHENTICATION

### Login Process

1. **Access the System**
   - URL: `http://[server-address]:8000/accounts/login/`
   - Use your assigned username and password

2. **Login Steps**
   ```
   Step 1: Enter your username
   Step 2: Enter your password
   Step 3: Click "Login" button
   Step 4: System automatically redirects to your role-specific dashboard
   ```

3. **Security Features**
   - ✅ Secure password authentication
   - ✅ Session timeout protection
   - ✅ CSRF protection against attacks
   - ✅ Role-based access control
   - ✅ Audit trail logging

### Password Requirements
- Minimum 8 characters
- Use strong, unique passwords
- Do not share credentials
- Report suspected security issues immediately

---

## 👥 USER ROLES & PERMISSIONS

### Administrative Roles

#### **Super Admin**
- **Username**: `admin`
- **Access**: Complete system control
- **Responsibilities**: System configuration, user management, oversight

#### **QA (Quality Assurance)**
- **Username**: `qa_user`
- **Access**: BMR creation, quality reviews, final approvals
- **Responsibilities**: 
  - Create BMRs
  - Review production quality
  - Final batch approval/rejection

#### **Regulatory Officer**
- **Username**: `regulatory_user`
- **Access**: Regulatory approvals, compliance oversight
- **Responsibilities**:
  - BMR regulatory approval
  - Compliance monitoring
  - Documentation review

### Production Roles

#### **Production Manager**
- **Username**: `production_manager`
- **Access**: Production planning, resource allocation
- **Responsibilities**:
  - Request BMRs from QA
  - Manage production schedules
  - Resource planning

#### **Store Manager (Raw Materials)**
- **Username**: `store_manager`
- **Access**: Raw material management and release
- **Responsibilities**:
  - Release raw materials for production
  - Inventory management
  - Material quality verification

#### **Material Dispensing Operator**
- **Username**: `dispensing_operator`
- **Access**: Material dispensing operations
- **Responsibilities**:
  - Dispense materials according to BMR
  - Record material usage
  - Maintain dispensing records

### Production Operators

#### **Mixing Operator**
- **Username**: `mixing_operator`
- **Access**: Mixing phase operations
- **Responsibilities**:
  - Execute mixing operations
  - Monitor mixing parameters
  - Record process data

#### **Granulation Operator**
- **Username**: `granulation_operator`
- **Access**: Granulation phase operations
- **Responsibilities**:
  - Perform granulation process
  - Monitor equipment parameters
  - Quality checks during process

#### **Blending Operator**
- **Username**: `blending_operator`
- **Access**: Blending phase operations
- **Responsibilities**:
  - Execute blending operations
  - Ensure uniform mixing
  - Process parameter monitoring

#### **Compression Operator**
- **Username**: `compression_operator`
- **Access**: Compression phase operations
- **Responsibilities**:
  - Operate compression equipment
  - Monitor tablet quality
  - Record compression parameters

#### **Coating Operator**
- **Username**: `coating_operator`
- **Access**: Coating phase operations (tablets only)
- **Responsibilities**:
  - Apply tablet coatings
  - Monitor coating quality
  - Equipment maintenance

#### **Other Production Operators**
- **Drying Operator**: `drying_operator` (capsules)
- **Filling Operator**: `filling_operator` (capsules/tubes)
- **Tube Filling Operator**: `tube_filling_operator` (ointments)
- **Sorting Operator**: `sorting_operator`
- **Packing Operator**: `packing_operator`

### Quality Control

#### **QC Officer**
- **Username**: `qc_user`
- **Access**: Quality control testing and approvals
- **Responsibilities**:
  - Perform QC tests
  - Approve/reject phases
  - Quality documentation

### Storage & Packaging

#### **Packaging Store**
- **Username**: `packaging_store`
- **Access**: Packaging material management
- **Responsibilities**:
  - Release packaging materials
  - Packaging inventory management

#### **Finished Goods Store**
- **Username**: `finished_goods_store`
- **Access**: Finished goods storage and management
- **Responsibilities**:
  - Store finished products
  - Inventory management
  - Dispatch coordination

---

## 🚀 GETTING STARTED

### First Login

1. **Receive Credentials**
   - Get username and password from system administrator
   - Verify your role assignment

2. **Initial Login**
   ```
   1. Navigate to login page
   2. Enter credentials
   3. System redirects to your dashboard
   4. Familiarize yourself with your dashboard layout
   ```

3. **Dashboard Orientation**
   - Review your assigned tasks
   - Check pending phases
   - Understand available actions

### System Requirements
- Modern web browser (Chrome, Firefox, Edge)
- Stable internet connection
- Screen resolution: 1024x768 minimum

---

## 🎛️ DASHBOARD NAVIGATION

### Common Dashboard Elements

#### **Header Section**
- Company logo and name
- User information
- Logout button
- Navigation menu

#### **Main Content Area**
- Task summaries
- Active phases
- Recent activities
- Performance metrics

#### **Action Buttons**
- Start Phase
- Complete Phase
- View Details
- Add Comments

### Role-Specific Dashboards

#### **Admin Dashboard Features**
- System overview statistics
- User management
- System health monitoring
- Production timeline
- Export capabilities

#### **Production Operator Dashboard Features**
- Assigned phases
- Current tasks
- Phase timers
- Machine selection
- Progress tracking

#### **QA Dashboard Features**
- BMR creation forms
- Quality review queue
- Approval workflows
- Compliance reports

#### **QC Dashboard Features**
- Testing queue
- Test results entry
- Approval/rejection actions
- Quality reports

---

## 🔄 CORE WORKFLOWS

### BMR (Batch Manufacturing Record) Workflow

```
1. Production Manager → Request BMR from QA
2. QA → Create BMR with product specifications
3. Regulatory → Review and approve BMR
4. Store Manager → Release raw materials
5. Production Phases → Execute according to BMR
6. QC → Quality testing at checkpoints
7. Final QA → Review and approve completed batch
8. Finished Goods Store → Store final product
```

### Product Type Workflows

#### **Tablets (Normal)**
```
Material Dispensing → Granulation → Blending → Compression → [Optional: Coating] → Blister Packing → Finished Goods
```

#### **Tablets (Type 2)**
```
Material Dispensing → Granulation → Blending → Compression → [Optional: Coating] → Bulk Packing → Finished Goods
```

#### **Capsules**
```
Material Dispensing → Drying → Blending → Filling → Blister Packing → Finished Goods
```

#### **Ointments**
```
Material Dispensing → Mixing → Tube Filling → Finished Goods
```

---

## 📝 DATA INPUT REQUIREMENTS

### Initial System Setup Data

#### **Products**
Required product information:
- Product name
- Product type (Tablet, Capsule, Ointment)
- Formulation details
- Batch size specifications
- Manufacturing instructions

#### **Users**
Required user information:
- Full name
- Username
- Role assignment
- Contact information
- Access permissions

#### **Machines**
Required machine information:
- Machine name
- Machine type (granulation, compression, etc.)
- Capacity specifications
- Maintenance schedules
- Operating parameters

#### **Materials**
Required material information:
- Material name
- Material type (raw material, packaging)
- Supplier information
- Storage requirements
- Quality specifications

### Operational Data Entry

#### **BMR Creation (QA Role)**
Required fields:
- Product selection
- Batch number (auto-generated: XXX-YYYY format)
- Batch size
- Manufacturing date
- Expiry date
- Special instructions
- Quality parameters

#### **Phase Execution (Operators)**
Required data during phase execution:
- Start time (automatic)
- Machine selection (where applicable)
- Process parameters
- Quality observations
- Completion time (automatic)
- Operator comments

#### **Quality Control (QC Role)**
Required QC data:
- Test results
- Pass/fail status
- Deviation notes
- Corrective actions
- Approval/rejection decision

### Batch Numbering System
- Format: **XXX-YYYY**
- Example: **001-2025** (1st batch of 2025)
- System auto-generates sequential numbers
- Unique per year

---

## 🏭 PRODUCTION PROCESS MANAGEMENT

### Starting a Production Phase

1. **Phase Assignment**
   - System assigns phases based on your role
   - Phases appear in your dashboard when ready

2. **Starting a Phase**
   ```
   Step 1: Review phase details
   Step 2: Select required machine (if applicable)
   Step 3: Click "Start Phase"
   Step 4: Enter start comments
   Step 5: Confirm start action
   ```

3. **During Phase Execution**
   - Monitor phase timer
   - Record process observations
   - Handle any deviations
   - Communicate issues to supervisors

4. **Completing a Phase**
   ```
   Step 1: Ensure all process steps completed
   Step 2: Click "Complete Phase"
   Step 3: Enter completion comments
   Step 4: Record any breakdown/changeover time
   Step 5: Confirm completion
   ```

### Machine Management

#### **Machine Selection**
Required for these phases:
- Granulation
- Blending
- Compression
- Coating
- Blister Packing
- Bulk Packing
- Filling (capsules)

#### **Machine Data Recording**
- Breakdown occurrences and duration
- Changeover times
- Maintenance requirements
- Performance parameters

### Phase Timer System

#### **Timer Features**
- Automatic start when phase begins
- Real-time countdown display
- Warning alerts approaching deadlines
- Overrun notifications

#### **Timer Status Colors**
- 🟢 **Green**: Normal operation
- 🟡 **Yellow**: Approaching deadline (warning)
- 🔴 **Red**: Deadline exceeded
- 🔴 **Dark Red**: Significant overrun

---

## 🔬 QUALITY CONTROL PROCEDURES

### QC Checkpoints

Quality control testing occurs at these stages:
- **Post-Mixing QC**: After mixing operations
- **Post-Blending QC**: After blending completion
- **Post-Compression QC**: After tablet compression
- **Final QA**: Before finished goods storage

### QC Testing Process

1. **Receive Testing Assignment**
   - Batch appears in QC dashboard
   - Review testing requirements
   - Prepare testing materials

2. **Perform Tests**
   - Execute required quality tests
   - Record test results
   - Document any deviations

3. **Decision Making**
   ```
   Pass: Batch continues to next phase
   Fail: Batch sent back for rework or quarantine
   ```

4. **Documentation**
   - Complete test records
   - Add approval signatures
   - Generate quality certificates

### Quality Rollback Process

If QC testing fails:
1. Batch status changes to "failed QC"
2. Batch returns to previous production phase
3. Investigation initiated
4. Corrective actions implemented
5. Re-testing after corrections

---

## ❗ TROUBLESHOOTING

### Common Login Issues

#### **Problem**: Login page not loading
**Solution**:
- Check internet connection
- Clear browser cache
- Try different browser
- Contact IT support

#### **Problem**: Invalid credentials error
**Solution**:
- Verify username and password
- Check caps lock
- Contact administrator for password reset
- Ensure account is active

#### **Problem**: Dashboard not loading after login
**Solution**:
- Wait for complete page load (may take few seconds)
- Check browser console for errors
- Try logging out and back in
- Contact technical support

### Performance Issues

#### **Problem**: Slow dashboard loading
**Solution**:
- Check internet speed
- Clear browser cache
- Close unnecessary browser tabs
- Contact IT if problem persists

#### **Problem**: Form submission failures
**Solution**:
- Ensure all required fields completed
- Check internet connection
- Try submitting again
- Save work frequently

### Data Entry Issues

#### **Problem**: Cannot start phase
**Solution**:
- Verify previous phase completed
- Check if machine selection required
- Ensure proper permissions
- Contact supervisor if issue persists

#### **Problem**: Missing data or phases
**Solution**:
- Refresh dashboard
- Check BMR status
- Verify role assignments
- Contact system administrator

---

## 💡 BEST PRACTICES

### Security Best Practices

1. **Password Management**
   - Use strong, unique passwords
   - Never share login credentials
   - Log out when finished working
   - Report security concerns immediately

2. **Data Protection**
   - Save work frequently
   - Double-check data entry
   - Report system errors promptly
   - Follow data backup procedures

### Operational Best Practices

1. **Phase Management**
   - Start phases promptly when assigned
   - Complete phases within expected timeframes
   - Record accurate process data
   - Communicate issues immediately

2. **Quality Assurance**
   - Follow all QC procedures
   - Document deviations properly
   - Maintain equipment properly
   - Keep accurate records

3. **Communication**
   - Use comment fields effectively
   - Report problems to supervisors
   - Coordinate with other operators
   - Follow escalation procedures

### Data Entry Best Practices

1. **Accuracy**
   - Double-check all entries
   - Use standard units of measurement
   - Record data in real-time
   - Verify calculations

2. **Completeness**
   - Fill all required fields
   - Add meaningful comments
   - Document any deviations
   - Include relevant observations

3. **Timeliness**
   - Enter data promptly
   - Don't delay phase completions
   - Update status regularly
   - Meet deadline requirements

---

## 📞 SUPPORT & CONTACTS

### Technical Support
- **System Issues**: Contact IT Department
- **Login Problems**: Contact System Administrator
- **Training Questions**: Contact Training Coordinator

### Operational Support
- **Production Issues**: Contact Production Manager
- **Quality Questions**: Contact QA Manager
- **Regulatory Issues**: Contact Regulatory Affairs

### Emergency Contacts
- **System Down**: IT Emergency Line
- **Production Emergency**: Production Manager
- **Quality Emergency**: QA Manager

---

## 📊 SYSTEM PERFORMANCE METRICS

### Expected Performance Standards
- **Login Time**: < 3 seconds
- **Dashboard Loading**: < 5 seconds
- **Phase Completion**: Within scheduled timeframes
- **Data Entry**: Real-time recording
- **System Availability**: 99.9% uptime

### Performance Monitoring
- System automatically tracks all activities
- Performance reports available to managers
- Regular system health checks
- Continuous improvement processes

---

## 🎯 CONCLUSION

The KPI Operations System is designed to streamline pharmaceutical production operations while maintaining the highest quality and compliance standards. 

### Key Success Factors:
1. **Proper Training**: Complete this training thoroughly
2. **Role Understanding**: Know your responsibilities
3. **System Navigation**: Practice using your dashboard
4. **Data Quality**: Maintain accurate records
5. **Communication**: Report issues promptly
6. **Continuous Learning**: Stay updated with system changes

### System Benefits:
- ✅ Improved production efficiency
- ✅ Enhanced quality control
- ✅ Complete audit trails
- ✅ Regulatory compliance
- ✅ Real-time visibility
- ✅ Reduced errors
- ✅ Better resource management

### Remember:
- The system is designed to help you work more efficiently
- Your role is crucial to overall production success
- Quality and safety are top priorities
- Continuous improvement is everyone's responsibility

---

**For additional training or questions, contact your supervisor or the training department.**

**System Version**: v1.0
**Last Updated**: November 2025
**Document Type**: User Training Manual

---

*© 2025 Kampala Pharmaceutical Industries - Operations System*