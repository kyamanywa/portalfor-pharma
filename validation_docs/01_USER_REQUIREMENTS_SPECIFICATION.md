# USER REQUIREMENTS SPECIFICATION (URS)
## Kampala Pharmaceutical Industries - Operations Management System

---

**Document Information**

| Item | Details |
|------|---------|
| Document Number | URS-KPI-OPS-001 |
| Version | 1.0 |
| Date | February 5, 2026 |
| System Name | KPI Operations Management System |
| Prepared By | System Development Team |
| Approved By | QA Manager / IT Manager |
| Status | Draft - Pending Approval |

---

## TABLE OF CONTENTS

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Regulatory Requirements](#3-regulatory-requirements)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [User Roles and Access](#6-user-roles-and-access)
7. [Data Management Requirements](#7-data-management-requirements)
8. [Security Requirements](#8-security-requirements)
9. [Validation Requirements](#9-validation-requirements)
10. [Appendices](#10-appendices)

---

## 1. INTRODUCTION

### 1.1 Purpose
This User Requirements Specification (URS) document defines the functional and non-functional requirements for the Kampala Pharmaceutical Industries Operations Management System. The system manages the complete pharmaceutical production lifecycle from Batch Manufacturing Record (BMR) creation through finished goods storage.

### 1.2 Scope
The system covers:
- BMR lifecycle management
- Production workflow automation
- Quality control and quarantine management
- Material dispensing and tracking
- Finished goods storage management
- Real-time production monitoring
- Regulatory compliance documentation

### 1.3 Intended Use
The system is intended for use in pharmaceutical manufacturing operations to:
- Ensure GMP compliance
- Track batch genealogy
- Maintain electronic batch records
- Monitor production efficiency
- Support regulatory inspections
- Enable data-driven decision making

### 1.4 References
- 21 CFR Part 11 - Electronic Records and Electronic Signatures (FDA)
- EU GMP Annex 11 - Computerized Systems
- WHO Technical Report Series No. 996, Annex 5
- PIC/S Good Practices for Computerized Systems
- GAMP 5 - A Risk-Based Approach to Compliant GxP Computerized Systems

---

## 2. SYSTEM OVERVIEW

### 2.1 System Description
The KPI Operations Management System is a web-based pharmaceutical manufacturing execution system that manages three product types:
1. **Ointments** - Topical pharmaceutical products
2. **Tablets** - Solid oral dosage forms (normal and type 2, coated/uncoated)
3. **Capsules** - Powder-filled capsule products

### 2.2 Key System Components
- **BMR Management Module** - Batch record creation and lifecycle
- **Workflow Engine** - Automated phase progression
- **Quality Management Module** - QC checkpoints and quarantine
- **Material Management** - Dispensing and inventory
- **Dashboard Module** - Role-based real-time monitoring
- **Reporting Module** - Production and quality reports
- **User Management** - Authentication and authorization

### 2.3 Technical Architecture
- **Platform**: Django 4.2.7 web framework
- **Database**: SQLite (development/testing), PostgreSQL (production)
- **Frontend**: HTML5, Bootstrap, JavaScript, Chart.js
- **API**: Django REST Framework
- **Server**: Waitress (testing), Gunicorn (production)

---

## 3. REGULATORY REQUIREMENTS

### 3.1 FDA Requirements (21 CFR Part 11)

**REG-001**: The system SHALL maintain electronic records equivalent to paper records for GMP purposes.

**REG-002**: The system SHALL implement electronic signatures with:
- Unique user identification
- Password authentication
- Time-stamped records
- Non-repudiation

**REG-003**: The system SHALL maintain complete audit trails showing:
- User identity
- Date and time of action
- Type of action performed
- Original and modified values (where applicable)

**REG-004**: The system SHALL prevent unauthorized access to records and operations.

**REG-005**: The system SHALL ensure data integrity through:
- Input validation
- Database constraints
- Prevention of data deletion
- Change tracking

### 3.2 GMP Requirements

**REG-006**: The system SHALL support cGMP manufacturing practices per WHO guidelines.

**REG-007**: The system SHALL maintain complete batch genealogy from raw materials to finished goods.

**REG-008**: The system SHALL track and document all manufacturing deviations.

**REG-009**: The system SHALL support regulatory inspection readiness.

**REG-010**: The system SHALL generate Certificate of Analysis (COA) documentation.

### 3.3 Data Integrity Requirements (ALCOA+)

**REG-011**: Data SHALL be Attributable (linked to user)
**REG-012**: Data SHALL be Legible (readable and permanent)
**REG-013**: Data SHALL be Contemporaneous (recorded at time of action)
**REG-014**: Data SHALL be Original (first recording)
**REG-015**: Data SHALL be Accurate (error-free and valid)
**REG-016**: Data SHALL be Complete (all required fields captured)
**REG-017**: Data SHALL be Consistent (sequential timestamps)
**REG-018**: Data SHALL be Enduring (retained throughout retention period)
**REG-019**: Data SHALL be Available (accessible for review)

---

## 4. FUNCTIONAL REQUIREMENTS

### 4.1 BMR Management

#### 4.1.1 BMR Creation

**BMR-001**: The system SHALL allow QA users to create new BMRs with:
- Unique BMR number (auto-generated)
- Manual batch number (format: XXX-YYYY validation)
- Manufacturing date
- Product selection
- Batch size (actual or standard)
- Manufacturing instructions
- Quality specifications

**BMR-002**: The system SHALL validate batch number uniqueness per product.

**BMR-003**: The system SHALL enforce batch number format (3 digits + 4 digits, e.g., 001-2025).

**BMR-004**: The system SHALL auto-populate product specifications from product master.

**BMR-005**: The system SHALL capture BMR creator identity and timestamp.

#### 4.1.2 BMR Approval Workflow

**BMR-006**: The system SHALL route newly created BMRs to Regulatory Affairs for approval.

**BMR-007**: The system SHALL allow Regulatory users to:
- Approve BMRs
- Reject BMRs with comments
- View complete BMR details

**BMR-008**: The system SHALL change BMR status to "Approved" upon regulatory approval.

**BMR-009**: The system SHALL capture approval/rejection user identity, timestamp, and comments.

**BMR-010**: The system SHALL notify Production Manager when BMR is approved.

#### 4.1.3 BMR Status Management

**BMR-011**: The system SHALL maintain following BMR statuses:
- Draft
- Submitted for Approval
- Approved
- Rejected
- In Production
- Completed
- Cancelled

**BMR-012**: The system SHALL enforce status transition rules:
- Draft → Submitted (by QA)
- Submitted → Approved/Rejected (by Regulatory)
- Approved → In Production (automatic on workflow start)
- In Production → Completed (when all phases complete)

**BMR-013**: The system SHALL prevent modification of approved BMRs except through authorized deviation process.

### 4.2 Workflow Management

#### 4.2.1 Product-Specific Workflows

**WF-001**: The system SHALL support Ointment workflow:
1. Mixing
2. QC Testing (post-mixing)
3. Tube Filling
4. Packaging Release
5. Secondary Packaging
6. Final QA
7. Finished Goods Storage

**WF-002**: The system SHALL support Tablet workflow (Normal):
1. Granulation
2. Blending
3. QC Testing (post-blending)
4. Compression
5. QC Testing (post-compression)
6. Sorting
7. Coating (conditional - if product is coated)
8. Packaging Release
9. Blister Packing
10. Secondary Packaging
11. Final QA
12. Finished Goods Storage

**WF-003**: The system SHALL support Tablet Type 2 workflow (uses Bulk Packing instead of Blister Packing).

**WF-004**: The system SHALL support Capsule workflow:
1. Drying
2. Blending
3. QC Testing (post-blending)
4. Filling
5. Sorting
6. Packaging Release
7. Blister Packing
8. Secondary Packaging
9. Final QA
10. Finished Goods Storage

**WF-005**: The system SHALL automatically determine workflow based on product type and specifications.

**WF-006**: The system SHALL skip coating phase for uncoated tablets.

**WF-007**: The system SHALL route Type 2 tablets to Bulk Packing instead of Blister Packing.

#### 4.2.2 Phase Execution

**WF-008**: The system SHALL create all required phases when BMR is approved.

**WF-009**: The system SHALL set initial phase status to "Pending".

**WF-010**: The system SHALL allow only authorized operators to execute phases based on role:
- Mixing Operator → Mixing phase
- Granulation Operator → Granulation phase
- Blending Operator → Blending phase
- Compression Operator → Compression phase
- Coating Operator → Coating phase
- Filling Operator → Filling phase
- Packing Operator → All packing phases
- (etc. for all operator types)

**WF-011**: The system SHALL capture for each phase execution:
- Start date/time
- End date/time
- Operator identity
- Machine used (where applicable)
- Process parameters
- Comments/observations
- Electronic signature

**WF-012**: The system SHALL automatically trigger next phase when current phase completes successfully.

**WF-013**: The system SHALL enforce sequential phase execution (cannot skip phases).

**WF-014**: The system SHALL allow only one active phase per batch at a time (except QC/quarantine).

#### 4.2.3 Phase Status Management

**WF-015**: The system SHALL maintain following phase statuses:
- Pending
- In Progress
- Completed
- Failed
- On Hold
- Cancelled

**WF-016**: The system SHALL transition phase status automatically:
- Pending → In Progress (when operator starts)
- In Progress → Completed (when operator completes successfully)
- In Progress → Failed (when QC rejects)
- Completed → Pending (when rolled back from QC failure)

**WF-017**: The system SHALL prevent re-execution of completed phases except through deviation management.

### 4.3 Quality Control Management

#### 4.3.1 QC Checkpoints

**QC-001**: The system SHALL implement mandatory QC checkpoints:
- After Mixing (for ointments)
- After Blending (for tablets and capsules)
- After Compression (for tablets)

**QC-002**: The system SHALL automatically place batch in quarantine when QC checkpoint is reached.

**QC-003**: The system SHALL allow QC users to:
- View quarantined batches
- Enter test results
- Approve batch for next phase
- Reject batch with reason

**QC-004**: The system SHALL capture QC test data:
- Test parameters
- Actual values
- Specification limits
- Pass/fail determination
- QC analyst identity
- Test date/time
- Comments

**QC-005**: The system SHALL support multiple QC test types per checkpoint.

#### 4.3.2 Quarantine Management

**QC-006**: The system SHALL automatically create quarantine record when batch reaches QC checkpoint.

**QC-007**: The system SHALL maintain quarantine statuses:
- In Quarantine
- Sample Requested
- Sample with QA
- Sample with QC
- Sample Approved
- Sample Failed
- Released to Next Phase

**QC-008**: The system SHALL allow production operators to request QC samples from quarantine.

**QC-009**: The system SHALL limit sample requests to maximum 2 per quarantine batch.

**QC-010**: The system SHALL route sample requests to QA for collection.

**QC-011**: The system SHALL allow QA users to:
- View sample requests
- Collect samples
- Record sample details
- Forward samples to QC

**QC-012**: The system SHALL allow QC users to:
- Receive samples from QA
- Enter test results
- Approve or fail samples

**QC-013**: The system SHALL allow quarantine manager to:
- Release batch to next phase (if approved)
- Proceed batch to next phase from quarantine
- View quarantine duration metrics

#### 4.3.3 Phase Rollback

**QC-014**: The system SHALL automatically rollback batch to previous phase when QC test fails.

**QC-015**: The system SHALL reset previous phase status to "Pending" upon rollback.

**QC-016**: The system SHALL maintain history of all rollback events.

**QC-017**: The system SHALL allow re-execution of failed phase after corrective actions.

**QC-018**: The system SHALL capture reason for failure and corrective actions taken.

### 4.4 Material Management

#### 4.4.1 Material Release

**MAT-001**: The system SHALL allow Store Manager to release raw materials for production.

**MAT-002**: The system SHALL capture material release data:
- BMR reference
- Material name/code
- Quantity released
- Batch/lot number
- Expiry date
- Release date/time
- Released by (user identity)

**MAT-003**: The system SHALL validate material availability before release.

**MAT-004**: The system SHALL track material traceability from receipt to finished goods.

#### 4.4.2 Material Dispensing

**MAT-005**: The system SHALL allow Dispensing Manager to dispense materials to production.

**MAT-006**: The system SHALL capture dispensing data:
- Material name
- Quantity dispensed
- Actual weight/volume
- Dispensing date/time
- Dispensed by (user identity)
- Production line/area

**MAT-007**: The system SHALL calculate material yield and reconciliation.

**MAT-008**: The system SHALL track packaging materials separately.

**MAT-009**: The system SHALL allow Packaging Store users to release packaging materials.

### 4.5 Finished Goods Management

**FGS-001**: The system SHALL automatically create finished goods inventory when batch completes all phases.

**FGS-002**: The system SHALL capture finished goods data:
- Batch number
- Product name
- Quantity available
- Unit of measure
- Manufacturing date
- Expiry date
- Storage location
- QA approval status

**FGS-003**: The system SHALL allow Finished Goods Store users to:
- View inventory
- Update quantities
- Record product releases
- Track storage conditions

**FGS-004**: The system SHALL track finished goods movements:
- Sales/releases
- Transfers
- Returns
- Destructions

**FGS-005**: The system SHALL maintain finished goods status:
- Stored
- Available for Sale
- Reserved
- Released/Sold
- Recalled

### 4.6 Dashboard and Reporting

#### 4.6.1 Role-Based Dashboards

**DASH-001**: The system SHALL provide unique dashboard for each user role.

**DASH-002**: The system SHALL display only information relevant to user role.

**DASH-003**: The system SHALL provide real-time production status updates.

**DASH-004**: The system SHALL display:
- Active batches
- Pending tasks
- Completed tasks
- Alerts and notifications
- Production metrics

#### 4.6.2 Analytics and Metrics

**DASH-005**: The system SHALL calculate and display:
- Phase completion rates
- Average cycle times
- On-time delivery percentage
- Quality pass/fail rates
- Equipment utilization
- Batch yield percentages

**DASH-006**: The system SHALL provide filterable charts:
- Phase status overview (by product type, time period)
- Production trends
- Quality trends
- Timeline analysis

**DASH-007**: The system SHALL support custom date range filters.

#### 4.6.3 Reports

**REP-001**: The system SHALL generate Batch Manufacturing Record report containing:
- Header information
- Material usage
- Phase execution details
- QC test results
- Deviations
- Approvals and signatures

**REP-002**: The system SHALL generate production summary reports.

**REP-003**: The system SHALL generate quality control reports.

**REP-004**: The system SHALL generate batch timeline reports.

**REP-005**: The system SHALL generate audit trail reports.

**REP-006**: The system SHALL export reports in PDF and Excel formats.

### 4.7 User Management

#### 4.7.1 User Authentication

**USER-001**: The system SHALL require username and password for login.

**USER-002**: The system SHALL enforce password complexity rules:
- Minimum 8 characters
- Mix of letters and numbers
- Password expiry (configurable)

**USER-003**: The system SHALL lock accounts after failed login attempts (configurable).

**USER-004**: The system SHALL support two-factor authentication (optional).

**USER-005**: The system SHALL log all login/logout events.

**USER-006**: The system SHALL auto-logout after inactivity period (configurable).

#### 4.7.2 User Roles and Permissions

**USER-007**: The system SHALL support following user roles:
1. Admin
2. Quality Assurance (QA)
3. Regulatory Affairs
4. Production Manager
5. Store Manager
6. Dispensing Manager
7. Packaging Store
8. Finished Goods Store
9. Quality Control (QC)
10. Quarantine Manager
11. Mixing Operator
12. Tube Filling Operator
13. Granulation Operator
14. Blending Operator
15. Compression Operator
16. Coating Operator
17. Drying Operator
18. Filling Operator
19. Sorting Operator
20. Packing Operator
21. Dispensing Operator
22. Equipment Operator
23. Cleaning Operator

**USER-008**: The system SHALL enforce role-based access control (RBAC).

**USER-009**: The system SHALL prevent users from accessing functions outside their role.

**USER-010**: The system SHALL allow Admin users to:
- Create/modify/deactivate users
- Assign roles
- View system logs
- Configure system settings

#### 4.7.3 Electronic Signatures

**USER-011**: The system SHALL capture electronic signatures for critical actions:
- BMR creation
- BMR approval/rejection
- Phase completion
- QC approvals
- Material dispensing
- Finished goods release

**USER-012**: The system SHALL record with each signature:
- User full name
- User role
- Date and time (with timezone)
- Action being signed
- Meaning of signature (e.g., "Reviewed and Approved")

**USER-013**: The system SHALL require re-authentication for high-risk operations.

---

## 5. NON-FUNCTIONAL REQUIREMENTS

### 5.1 Performance Requirements

**PERF-001**: The system SHALL load dashboard pages within 3 seconds under normal load.

**PERF-002**: The system SHALL support minimum 20 concurrent users without performance degradation.

**PERF-003**: The system SHALL process phase transitions within 2 seconds.

**PERF-004**: The system SHALL generate reports within 10 seconds for standard batch size.

**PERF-005**: The system SHALL handle minimum 100 active batches simultaneously.

### 5.2 Availability Requirements

**AVAIL-001**: The system SHALL maintain 99% uptime during production hours.

**AVAIL-002**: The system SHALL support scheduled maintenance windows.

**AVAIL-003**: The system SHALL implement automatic database backups daily.

**AVAIL-004**: The system SHALL provide disaster recovery capability with maximum 24-hour recovery time.

### 5.3 Scalability Requirements

**SCALE-001**: The system SHALL scale to support 50+ concurrent users.

**SCALE-002**: The system SHALL handle 500+ batches per year.

**SCALE-003**: The system SHALL retain data for minimum 5 years (or per regulatory requirement).

**SCALE-004**: The system SHALL support addition of new product types without major system changes.

### 5.4 Usability Requirements

**USAB-001**: The system SHALL provide intuitive web-based interface.

**USAB-002**: The system SHALL be accessible from tablets and desktop computers.

**USAB-003**: The system SHALL support modern web browsers (Chrome, Firefox, Edge).

**USAB-004**: The system SHALL provide context-sensitive help.

**USAB-005**: The system SHALL display clear error messages with resolution guidance.

**USAB-006**: The system SHALL use consistent navigation across all modules.

### 5.5 Maintainability Requirements

**MAINT-001**: The system SHALL use standard Django framework conventions.

**MAINT-002**: The system SHALL maintain comprehensive inline code documentation.

**MAINT-003**: The system SHALL use version control (Git) for all code changes.

**MAINT-004**: The system SHALL support non-disruptive software updates.

**MAINT-005**: The system SHALL maintain detailed system documentation.

### 5.6 Compatibility Requirements

**COMPAT-001**: The system SHALL run on Windows Server and Linux operating systems.

**COMPAT-002**: The system SHALL support PostgreSQL database (production).

**COMPAT-003**: The system SHALL support SQLite database (development/testing).

**COMPAT-004**: The system SHALL provide REST API for future integrations.

**COMPAT-005**: The system SHALL support export of data in standard formats (PDF, Excel, CSV).

---

## 6. USER ROLES AND ACCESS

### 6.1 Access Control Matrix

| Function | Admin | QA | Regulatory | Prod Mgr | Store Mgr | QC | Operators | FGS |
|----------|-------|-----|------------|----------|-----------|-----|-----------|-----|
| Create BMR | ✓ | ✓ | - | - | - | - | - | - |
| Approve BMR | ✓ | - | ✓ | - | - | - | - | - |
| View BMR | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Execute Phase | - | - | - | - | - | - | ✓ | - |
| Release Materials | ✓ | - | - | - | ✓ | - | - | - |
| Dispense Materials | ✓ | - | - | - | - | - | ✓ | - |
| QC Testing | ✓ | ✓ | - | - | - | ✓ | - | - |
| Quarantine Mgmt | ✓ | ✓ | - | - | - | ✓ | - | - |
| FGS Management | ✓ | ✓ | - | - | - | - | - | ✓ |
| View Reports | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Generate Reports | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| User Management | ✓ | - | - | - | - | - | - | - |
| System Config | ✓ | - | - | - | - | - | - | - |

### 6.2 Data Access Restrictions

**ACCESS-001**: Users SHALL view only batches relevant to their role.

**ACCESS-002**: Users SHALL NOT access configuration data except Admin role.

**ACCESS-003**: Users SHALL NOT delete records (soft delete only by Admin).

**ACCESS-004**: Users SHALL view audit trails only for their own actions (except Admin/QA).

---

## 7. DATA MANAGEMENT REQUIREMENTS

### 7.1 Data Retention

**DATA-001**: The system SHALL retain all batch records for minimum 5 years.

**DATA-002**: The system SHALL retain audit trails for minimum 5 years.

**DATA-003**: The system SHALL retain user session logs for minimum 1 year.

**DATA-004**: The system SHALL implement archiving for records older than retention period.

### 7.2 Data Backup

**DATA-005**: The system SHALL perform automatic daily database backups.

**DATA-006**: The system SHALL store backups in secure offsite location.

**DATA-007**: The system SHALL test backup restoration quarterly.

**DATA-008**: The system SHALL maintain backup retention for minimum 30 days.

### 7.3 Data Integrity

**DATA-009**: The system SHALL implement database constraints to prevent invalid data.

**DATA-010**: The system SHALL validate all user inputs before database storage.

**DATA-011**: The system SHALL use database transactions to ensure atomicity.

**DATA-012**: The system SHALL prevent SQL injection and other security vulnerabilities.

**DATA-013**: The system SHALL implement database locking to prevent concurrent update conflicts.

### 7.4 Data Migration

**DATA-014**: The system SHALL support data export for migration purposes.

**DATA-015**: The system SHALL provide data import validation.

**DATA-016**: The system SHALL maintain data integrity during migrations.

---

## 8. SECURITY REQUIREMENTS

### 8.1 Authentication Security

**SEC-001**: The system SHALL hash and salt passwords using industry-standard algorithms.

**SEC-002**: The system SHALL NOT display passwords in plain text anywhere.

**SEC-003**: The system SHALL implement session timeout after 30 minutes inactivity.

**SEC-004**: The system SHALL log all authentication events.

### 8.2 Authorization Security

**SEC-005**: The system SHALL enforce principle of least privilege.

**SEC-006**: The system SHALL verify user permissions on every action.

**SEC-007**: The system SHALL prevent privilege escalation attacks.

### 8.3 Network Security

**SEC-008**: The system SHALL support HTTPS encryption for data transmission.

**SEC-009**: The system SHALL implement CSRF protection.

**SEC-010**: The system SHALL implement XSS protection.

**SEC-011**: The system SHALL restrict API access to authenticated users.

### 8.4 Audit Security

**SEC-012**: The system SHALL log all security-relevant events:
- Login/logout
- Failed authentication attempts
- Permission denied events
- Data modifications
- Configuration changes

**SEC-013**: The system SHALL protect audit logs from modification.

**SEC-014**: The system SHALL timestamp all log entries with timezone.

---

## 9. VALIDATION REQUIREMENTS

### 9.1 System Validation

**VAL-001**: The system SHALL be validated per GAMP 5 guidelines (Category 4).

**VAL-002**: The system SHALL have documented validation plan.

**VAL-003**: The system SHALL undergo Installation Qualification (IQ).

**VAL-004**: The system SHALL undergo Operational Qualification (OQ).

**VAL-005**: The system SHALL undergo Performance Qualification (PQ).

### 9.2 Change Control

**VAL-006**: All system changes SHALL be documented in change control system.

**VAL-007**: All changes SHALL be risk-assessed before implementation.

**VAL-008**: All changes SHALL be tested and validated before production release.

**VAL-009**: All changes SHALL be approved by QA/IT management.

### 9.3 Deviation Management

**VAL-010**: The system SHALL support deviation recording and tracking.

**VAL-011**: The system SHALL link deviations to affected batches.

**VAL-012**: The system SHALL track CAPA (Corrective and Preventive Actions).

---

## 10. APPENDICES

### Appendix A: Glossary of Terms

- **BMR**: Batch Manufacturing Record
- **QA**: Quality Assurance
- **QC**: Quality Control
- **FGS**: Finished Goods Store
- **GMP**: Good Manufacturing Practice
- **cGMP**: Current Good Manufacturing Practice
- **CFR**: Code of Federal Regulations
- **API**: Active Pharmaceutical Ingredient
- **SOP**: Standard Operating Procedure
- **CAPA**: Corrective and Preventive Action
- **OQ**: Operational Qualification
- **IQ**: Installation Qualification
- **PQ**: Performance Qualification
- **GAMP**: Good Automated Manufacturing Practice

### Appendix B: Acronyms

- **ALCOA+**: Attributable, Legible, Contemporaneous, Original, Accurate (+ Complete, Consistent, Enduring, Available)
- **RBAC**: Role-Based Access Control
- **REST**: Representational State Transfer
- **API**: Application Programming Interface
- **CSV**: Comma-Separated Values
- **PDF**: Portable Document Format
- **SQL**: Structured Query Language
- **HTTPS**: Hypertext Transfer Protocol Secure
- **CSRF**: Cross-Site Request Forgery
- **XSS**: Cross-Site Scripting

### Appendix C: Requirements Traceability

A complete traceability matrix linking URS requirements to FRS specifications and test cases is provided in separate document: **Traceability_Matrix.xlsx**

---

## APPROVAL SIGNATURES

| Role | Name | Signature | Date |
|------|------|-----------|------|
| QA Manager | _________________ | _________________ | __________ |
| IT Manager | _________________ | _________________ | __________ |
| Production Manager | _________________ | _________________ | __________ |
| Regulatory Manager | _________________ | _________________ | __________ |

---

**Document Control**
- Next Review Date: [6 months from approval]
- Document Location: [Quality Management System / IT Documentation]
- Revision History: Version 1.0 - Initial Release

---

**END OF DOCUMENT**
