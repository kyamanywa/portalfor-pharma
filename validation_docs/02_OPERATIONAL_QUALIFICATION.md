# OPERATIONAL QUALIFICATION (OQ)
## Kampala Pharmaceutical Industries - Operations Management System
## Test Protocol and Execution Records

---

**Document Information**

| Item | Details |
|------|---------|
| Document Number | OQ-KPI-OPS-001 |
| Version | 1.0 |
| Date | February 5, 2026 |
| System Name | KPI Operations Management System |
| Prepared By | Validation Team |
| Reviewed By | QA Manager |
| Approved By | IT Manager |
| Status | Draft - Ready for Execution |

---

## TABLE OF CONTENTS

1. [Introduction](#1-introduction)
2. [Test Scope](#2-test-scope)
3. [Test Environment](#3-test-environment)
4. [Test Execution Instructions](#4-test-execution-instructions)
5. [Test Cases - User Management](#5-test-cases-user-management)
6. [Test Cases - BMR Management](#6-test-cases-bmr-management)
7. [Test Cases - Workflow Engine](#7-test-cases-workflow-engine)
8. [Test Cases - Quality Control](#8-test-cases-quality-control)
9. [Test Cases - Material Management](#9-test-cases-material-management)
10. [Test Cases - Finished Goods](#10-test-cases-finished-goods)
11. [Test Cases - Security and Audit](#11-test-cases-security-and-audit)
12. [Test Summary](#12-test-summary)
13. [Appendices](#13-appendices)

---

## 1. INTRODUCTION

### 1.1 Purpose
This Operational Qualification (OQ) protocol verifies that the KPI Operations Management System functions according to specifications defined in the User Requirements Specification (URS) and Functional Requirements Specification (FRS).

### 1.2 Scope
OQ testing covers:
- All functional modules
- User roles and permissions
- Workflow automation
- Data validation rules
- System integrations
- Security controls
- Audit trail functionality

### 1.3 Prerequisites
Before executing OQ tests:
- ✅ Installation Qualification (IQ) completed and approved
- ✅ System installed on test server
- ✅ Database initialized with test data
- ✅ Test users created for all roles
- ✅ Sample products configured
- ✅ Test environment backed up

### 1.4 Test Execution Rules
- Tests must be executed in sequence within each module
- All fields marked "Required" must be tested
- Actual results must be documented for each test
- Failed tests must be documented with deviation number
- Re-testing required after bug fixes

---

## 2. TEST SCOPE

### 2.1 Modules to be Tested

| Module | Test Cases | Priority |
|--------|------------|----------|
| User Management | 15 | Critical |
| BMR Management | 25 | Critical |
| Workflow Engine | 30 | Critical |
| Quality Control | 20 | Critical |
| Material Management | 15 | High |
| Finished Goods | 12 | High |
| Dashboards | 10 | Medium |
| Reporting | 10 | Medium |
| Security & Audit | 15 | Critical |
| **TOTAL** | **152** | - |

### 2.2 Out of Scope
- Performance testing (covered in PQ)
- Load testing (covered in PQ)
- User interface design review
- Code review
- Network infrastructure testing

---

## 3. TEST ENVIRONMENT

### 3.1 System Configuration

| Component | Specification |
|-----------|--------------|
| Server OS | Windows Server 2022 / Ubuntu 22.04 |
| Python Version | 3.11+ |
| Django Version | 4.2.7 |
| Database | SQLite (test) / PostgreSQL (production) |
| Web Server | Waitress 3.0.2 |
| Browser | Chrome 120+, Firefox 121+, Edge 120+ |

### 3.2 Test Data

**Test Users Created:**
- admin_test (Admin)
- qa_test (Quality Assurance)
- reg_test (Regulatory Affairs)
- pm_test (Production Manager)
- qc_test (Quality Control)
- mix_op_test (Mixing Operator)
- gran_op_test (Granulation Operator)
- blend_op_test (Blending Operator)
- comp_op_test (Compression Operator)
- pack_op_test (Packing Operator)

**Test Products:**
- Paracetamol 500mg Tablets (Uncoated, Normal)
- Ibuprofen 200mg Tablets (Coated, Normal)
- Diclofenac Gel 1% (Ointment)
- Amoxicillin 250mg Capsules

---

## 4. TEST EXECUTION INSTRUCTIONS

### 4.1 How to Execute Tests

**For Each Test Case:**

1. **Read Prerequisites** - Ensure all preconditions are met
2. **Follow Test Steps** - Execute each step exactly as written
3. **Record Actual Result** - Document what actually happened
4. **Compare with Expected** - Check if actual matches expected result
5. **Mark Pass/Fail** - Circle appropriate result
6. **Sign and Date** - Tester must sign/date each test
7. **Document Deviations** - If failed, record deviation number

### 4.2 Test Result Codes

- **PASS** ✓ - Test met expected result exactly
- **FAIL** ✗ - Test did not meet expected result
- **N/A** - Test not applicable
- **BLOCKED** - Test cannot be executed due to blocking issue

### 4.3 Deviation Handling

If test fails:
1. Stop testing in that module
2. Create deviation record: DEV-OQ-[number]
3. Document:
   - Test case ID
   - Description of failure
   - Screenshots if applicable
   - Root cause (if known)
4. Assign to development team
5. Re-test after fix implemented

---

## 5. TEST CASES - USER MANAGEMENT

### TC-USER-001: Create New User Account

**Requirement ID**: USER-007, USER-008  
**Priority**: Critical  
**Tester**: _________________  
**Date**: _________________

**Objective**: Verify admin can create new user with all required fields.

**Prerequisites**:
- Logged in as admin_test user
- Navigate to User Management page

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click "Add User" button | Add User form displays |
| 2 | Enter username: "test_user_001" | Field accepts input |
| 3 | Enter first name: "Test" | Field accepts input |
| 4 | Enter last name: "User" | Field accepts input |
| 5 | Enter email: "test@example.com" | Field accepts input |
| 6 | Enter employee ID: "EMP-001" | Field accepts input |
| 7 | Select role: "Mixing Operator" | Dropdown shows selection |
| 8 | Enter department: "Production" | Field accepts input |
| 9 | Enter password: "Test@1234" | Field masks password |
| 10 | Enter password confirmation: "Test@1234" | Field masks password |
| 11 | Click "Save" button | Success message displays |
| 12 | Search for "test_user_001" | New user appears in list |
| 13 | Click on user to view details | All entered data displayed correctly |

**Actual Result**: _________________________________________________________________

**Status**: ⃝ PASS  ⃝ FAIL  ⃝ N/A  ⃝ BLOCKED

**Comments**: ____________________________________________________________________

**Tester Signature**: _________________ **Date**: _________  
**Reviewer Signature**: _________________ **Date**: _________

---

### TC-USER-002: Validate Required Fields

**Requirement ID**: USER-007  
**Priority**: Critical  
**Tester**: _________________  
**Date**: _________________

**Objective**: Verify system validates required fields when creating user.

**Prerequisites**:
- Logged in as admin_test user
- Navigate to Add User form

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Leave username blank | Field marked as required |
| 2 | Click "Save" without filling required fields | Error message: "This field is required" |
| 3 | Enter username only: "incomplete_user" | Form still shows validation errors |
| 4 | Attempt to save | System prevents save, shows error messages |
| 5 | Fill all required fields correctly | Form validates successfully |
| 6 | Click "Save" | User created successfully |

**Actual Result**: _________________________________________________________________

**Status**: ⃝ PASS  ⃝ FAIL  ⃝ N/A  ⃝ BLOCKED

**Tester Signature**: _________________ **Date**: _________

---

### TC-USER-003: Validate Employee ID Uniqueness

**Requirement ID**: USER-007  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create user with employee ID "EMP-999" | User created successfully |
| 2 | Attempt to create another user with same employee ID | Error: "Employee ID must be unique" |
| 3 | System prevents duplicate creation | Duplicate not created |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-USER-004: User Login with Valid Credentials

**Requirement ID**: USER-001  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to login page | Login form displays |
| 2 | Enter username: "test_user_001" | Field accepts input |
| 3 | Enter password: "Test@1234" | Field masks password |
| 4 | Click "Login" button | User logged in successfully |
| 5 | Verify role-based dashboard displays | Dashboard for "Mixing Operator" role shown |
| 6 | Check user name in header | "Test User" displayed |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-USER-005: User Login with Invalid Credentials

**Requirement ID**: USER-001, SEC-001  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to login page | Login form displays |
| 2 | Enter username: "test_user_001" | Field accepts input |
| 3 | Enter password: "WrongPassword123" | Field masks password |
| 4 | Click "Login" button | Error message: "Invalid username or password" |
| 5 | User remains on login page | Login form still displayed |
| 6 | User is NOT logged in | No dashboard access |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-USER-006: Account Lockout After Failed Attempts

**Requirement ID**: USER-003, SEC-001  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Attempt login with wrong password | Login fails |
| 2 | Attempt login with wrong password (2nd time) | Login fails |
| 3 | Attempt login with wrong password (3rd time) | Login fails |
| 4 | Attempt login with wrong password (4th time) | Account locked message displays |
| 5 | Attempt login with CORRECT password | Login prevented, account locked |
| 6 | Admin unlocks account | Account status changed to active |
| 7 | Attempt login with correct password | Login successful |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-USER-007: Session Timeout After Inactivity

**Requirement ID**: USER-006, SEC-003  
**Priority**: High

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as test_user_001 | Login successful |
| 2 | Note current time | Time recorded |
| 3 | Leave browser idle for 30 minutes | No user interaction |
| 4 | Attempt to perform action after 30 min | Session timeout message displays |
| 5 | User redirected to login page | Login form shown |
| 6 | Login again | New session created |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-USER-008: Role-Based Dashboard Display

**Requirement ID**: DASH-001, DASH-002  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as QA user (qa_test) | QA dashboard displays |
| 2 | Verify "Create BMR" button visible | Button present |
| 3 | Verify no production phase buttons | Operator buttons NOT visible |
| 4 | Logout | Login page displays |
| 5 | Login as Mixing Operator (mix_op_test) | Mixing Operator dashboard displays |
| 6 | Verify "Start Mixing" button visible | Button present |
| 7 | Verify "Create BMR" button NOT visible | Button not present |
| 8 | Verify cannot access QA functions | Access denied |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-USER-009: Modify User Details

**Requirement ID**: USER-010  
**Priority**: Medium

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as admin | Admin dashboard displays |
| 2 | Navigate to Users list | Users list displays |
| 3 | Click on test_user_001 | User details page displays |
| 4 | Click "Edit" button | Edit form displays |
| 5 | Change department to "Quality" | Field accepts change |
| 6 | Change phone number to "0700123456" | Field accepts input |
| 7 | Click "Save" | Success message displays |
| 8 | Verify changes saved | Updated information displays |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-USER-010: Deactivate User Account

**Requirement ID**: USER-010  
**Priority**: High

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as admin | Admin dashboard displays |
| 2 | Select test_user_001 | User details display |
| 3 | Uncheck "Is Active" checkbox | Checkbox unchecked |
| 4 | Click "Save" | User deactivated successfully |
| 5 | Logout | Login page displays |
| 6 | Attempt login as test_user_001 | Login denied, "Account inactive" message |

**Status**: ⃝ PASS  ⃝ FAIL

---

## 6. TEST CASES - BMR MANAGEMENT

### TC-BMR-001: Create BMR with Valid Data

**Requirement ID**: BMR-001, BMR-005  
**Priority**: Critical

**Objective**: Verify QA user can create new BMR with all required information.

**Prerequisites**:
- Logged in as qa_test user
- Test product "Paracetamol 500mg Tablets" configured

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to BMR Management page | BMR list displays |
| 2 | Click "Create New BMR" button | BMR creation form displays |
| 3 | Select product: "Paracetamol 500mg Tablets" | Product selected, specs auto-populated |
| 4 | Enter batch number: "001-2026" | Field accepts format |
| 5 | Enter manufacturing date: "05-Feb-2026" | Date picker accepts date |
| 6 | Verify standard batch size auto-populated | Batch size displays from product master |
| 7 | Enter actual batch size: "50000" (if different) | Field accepts input |
| 8 | Enter manufacturing instructions | Text area accepts input |
| 9 | Enter quality specifications | Text area accepts input |
| 10 | Click "Save as Draft" | BMR saved with status "Draft" |
| 11 | Verify BMR number auto-generated | Unique BMR number assigned (e.g., BMR-000001) |
| 12 | Verify created_by = qa_test | Creator recorded |
| 13 | Verify created_date = current timestamp | Timestamp recorded |

**Actual Result**: _________________________________________________________________

**Status**: ⃝ PASS  ⃝ FAIL  ⃝ N/A  ⃝ BLOCKED

**Tester Signature**: _________________ **Date**: _________

---

### TC-BMR-002: Validate Batch Number Format

**Requirement ID**: BMR-003  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Enter invalid batch number: "123" | Validation error displays |
| 2 | Enter invalid batch number: "ABCD-2026" | Error: "Format must be XXX-YYYY (digits only)" |
| 3 | Enter invalid batch number: "1-2026" | Error: "Must be 3 digits - 4 digits" |
| 4 | Enter valid batch number: "002-2026" | Validation passes, no error |
| 5 | Save BMR | BMR saved successfully |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-BMR-003: Validate Batch Number Uniqueness per Product

**Requirement ID**: BMR-002  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create BMR for "Paracetamol 500mg" with batch "003-2026" | BMR created successfully |
| 2 | Attempt to create another BMR for same product with batch "003-2026" | Error: "Batch number already exists for this product" |
| 3 | Create BMR for "Ibuprofen 200mg" with batch "003-2026" | BMR created successfully (different product, same batch OK) |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-BMR-004: Submit BMR for Approval

**Requirement ID**: BMR-006  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open BMR in "Draft" status | BMR details display |
| 2 | Click "Submit for Approval" button | Confirmation dialog displays |
| 3 | Confirm submission | BMR status changes to "Submitted for Approval" |
| 4 | Verify submitted_date recorded | Timestamp recorded |
| 5 | Verify "Edit" button disabled | BMR cannot be edited in submitted state |
| 6 | Verify notification sent to Regulatory | Email/notification sent |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-BMR-005: Approve BMR (Regulatory)

**Requirement ID**: BMR-007, BMR-008, BMR-009  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Logout QA user, login as reg_test | Regulatory dashboard displays |
| 2 | Navigate to "Pending Approvals" | BMRs with "Submitted" status display |
| 3 | Click on BMR to review | BMR details display |
| 4 | Review all information | Information correct and complete |
| 5 | Enter approval comments: "Approved for production" | Comments field accepts input |
| 6 | Click "Approve" button | Confirmation dialog displays |
| 7 | Confirm approval | BMR status changes to "Approved" |
| 8 | Verify approved_by = reg_test | Approver identity recorded |
| 9 | Verify approved_date = current timestamp | Approval timestamp recorded |
| 10 | Verify workflow auto-initialized | Production phases created |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-BMR-006: Reject BMR (Regulatory)

**Requirement ID**: BMR-007, BMR-009  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as reg_test | Regulatory dashboard displays |
| 2 | Select BMR to reject | BMR details display |
| 3 | Click "Reject" button | Rejection dialog displays |
| 4 | Attempt to reject without comments | Validation error: "Comments required for rejection" |
| 5 | Enter rejection reason: "Incomplete manufacturing instructions" | Comments accepted |
| 6 | Confirm rejection | BMR status changes to "Rejected" |
| 7 | Verify regulatory_comments saved | Comments visible in BMR |
| 8 | Verify rejected_by = reg_test | Rejector identity recorded |
| 9 | Verify notification sent to QA | QA user notified |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-BMR-007: View BMR Details (All Roles)

**Requirement ID**: DASH-001  
**Priority**: High

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as qa_test | BMR visible in dashboard |
| 2 | Login as mix_op_test | BMR visible if assigned to mixing |
| 3 | Login as qc_test | BMR visible in QC dashboard |
| 4 | Verify all users can VIEW BMR | Read access granted |
| 5 | Verify only authorized users can EDIT | Write access restricted |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-BMR-008: BMR Number Auto-Generation

**Requirement ID**: BMR-001  
**Priority**: Medium

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create first BMR | BMR number = "BMR-000001" or similar format |
| 2 | Create second BMR | BMR number increments: "BMR-000002" |
| 3 | Create third BMR | BMR number increments: "BMR-000003" |
| 4 | Verify no duplicate BMR numbers | All BMR numbers unique |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-BMR-009: Prevent Edit of Approved BMR

**Requirement ID**: BMR-013  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Select approved BMR | BMR details display |
| 2 | Verify "Edit" button disabled or hidden | Cannot edit approved BMR |
| 3 | Attempt direct URL edit (if applicable) | Access denied, redirect to view page |
| 4 | Verify data integrity maintained | No modifications allowed |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-BMR-010: BMR Status Transitions

**Requirement ID**: BMR-012  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create BMR | Status = "Draft" |
| 2 | Submit BMR | Status = "Submitted for Approval" |
| 3 | Approve BMR | Status = "Approved" |
| 4 | Start production (phase execution) | Status = "In Production" |
| 5 | Complete all phases | Status = "Completed" |
| 6 | Verify invalid transitions prevented | Cannot skip status steps |

**Status**: ⃝ PASS  ⃝ FAIL

---

## 7. TEST CASES - WORKFLOW ENGINE

### TC-WF-001: Workflow Initialization for Ointment

**Requirement ID**: WF-001, WF-005, WF-008  
**Priority**: Critical

**Objective**: Verify correct workflow phases created when ointment BMR is approved.

**Prerequisites**:
- Product "Diclofenac Gel 1%" (Ointment) configured
- BMR created and approved

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Approve BMR for ointment product | BMR approved successfully |
| 2 | Navigate to workflow phases for this BMR | Phases list displays |
| 3 | Verify phase sequence: | |
|  | - Mixing | Phase created, status "Pending" |
|  | - QC Testing | Phase created, status "Pending" |
|  | - Tube Filling | Phase created, status "Pending" |
|  | - Packaging Release | Phase created, status "Pending" |
|  | - Secondary Packaging | Phase created, status "Pending" |
|  | - Final QA | Phase created, status "Pending" |
|  | - Finished Goods Storage | Phase created, status "Pending" |
| 4 | Verify phase order numbers | Phases numbered 1-7 sequentially |
| 5 | Verify no tablet/capsule phases created | Only ointment phases present |

**Actual Result**: _________________________________________________________________

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-002: Workflow Initialization for Uncoated Tablet

**Requirement ID**: WF-002, WF-005, WF-006  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Approve BMR for "Paracetamol 500mg" (uncoated) | BMR approved |
| 2 | Verify phases created: | |
|  | - Granulation | Created |
|  | - Blending | Created |
|  | - QC Testing (post-blending) | Created |
|  | - Compression | Created |
|  | - QC Testing (post-compression) | Created |
|  | - Sorting | Created |
|  | - Packaging Release | Created |
|  | - Blister Packing | Created |
|  | - Secondary Packaging | Created |
|  | - Final QA | Created |
|  | - Finished Goods Storage | Created |
| 3 | Verify Coating phase NOT created | Coating skipped for uncoated product |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-003: Workflow Initialization for Coated Tablet

**Requirement ID**: WF-002, WF-005, WF-006  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Approve BMR for "Ibuprofen 200mg" (coated) | BMR approved |
| 2 | Verify Coating phase IS created | Coating phase present |
| 3 | Verify Coating comes after Sorting | Phase order correct |
| 4 | Verify Packaging Release after Coating | Sequence correct |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-004: Workflow Initialization for Tablet Type 2

**Requirement ID**: WF-003, WF-007  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create and approve BMR for Tablet Type 2 product | BMR approved |
| 2 | Verify Bulk Packing phase created | Bulk Packing present |
| 3 | Verify Blister Packing NOT created | Blister Packing absent |
| 4 | Verify Bulk Packing after Packaging Release | Phase order correct |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-005: Workflow Initialization for Capsule

**Requirement ID**: WF-004  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Approve BMR for "Amoxicillin 250mg Capsules" | BMR approved |
| 2 | Verify capsule workflow phases: | |
|  | - Drying | Created |
|  | - Blending | Created |
|  | - QC Testing | Created |
|  | - Filling | Created |
|  | - Sorting | Created |
|  | - Packaging Release | Created |
|  | - Blister Packing | Created |
|  | - Secondary Packaging | Created |
|  | - Final QA | Created |
|  | - Finished Goods Storage | Created |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-006: Execute Phase - Mixing Operator

**Requirement ID**: WF-010, WF-011  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as mix_op_test | Mixing Operator dashboard displays |
| 2 | Navigate to "Pending Batches" | Batches ready for mixing display |
| 3 | Select batch for mixing | Batch details display |
| 4 | Click "Start Mixing" button | Phase status changes to "In Progress" |
| 5 | Verify start_time recorded | Current timestamp captured |
| 6 | Verify operator recorded | mix_op_test identity saved |
| 7 | Enter process parameters: | |
|  | - Mixer speed: "150 RPM" | Field accepts input |
|  | - Mixing time: "30 minutes" | Field accepts input |
|  | - Temperature: "25°C" | Field accepts input |
| 8 | Select machine: "Mixer-01" | Machine dropdown selection |
| 9 | Enter observations/comments | Text area accepts input |
| 10 | Click "Complete Phase" button | Confirmation dialog displays |
| 11 | Provide electronic signature (re-auth) | Password prompt displays |
| 12 | Confirm completion | Phase status changes to "Completed" |
| 13 | Verify end_time recorded | Current timestamp captured |
| 14 | Verify next phase auto-triggered | Next phase status changes to "Pending" (ready) |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-007: Enforce Role-Based Phase Access

**Requirement ID**: WF-010  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as mix_op_test | Mixing Operator dashboard |
| 2 | Attempt to access Granulation phase | Access denied or button not visible |
| 3 | Attempt direct URL to granulation | Redirect with "Permission denied" message |
| 4 | Login as gran_op_test | Granulation Operator dashboard |
| 5 | Verify Granulation phase accessible | Can start/complete granulation |
| 6 | Verify Mixing phase NOT accessible | Cannot access mixing functions |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-008: Sequential Phase Execution

**Requirement ID**: WF-013  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as Compression Operator | Dashboard displays |
| 2 | View batch that hasn't completed Blending yet | Compression phase shows "Waiting for previous phase" |
| 3 | Attempt to start Compression | Action blocked, error message displays |
| 4 | Complete Blending phase | Blending marked complete |
| 5 | Return to Compression phase | Compression now shows "Ready to Start" |
| 6 | Start Compression | Phase starts successfully |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-009: Prevent Concurrent Phase Execution

**Requirement ID**: WF-014  
**Priority**: High

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Operator 1 starts Mixing phase | Status = "In Progress" |
| 2 | Operator 2 attempts to start same Mixing phase | Error: "Phase already in progress" |
| 3 | Operator 1 completes Mixing | Status = "Completed" |
| 4 | Verify only one execution record | Single start/end timestamp pair |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-010: Capture Phase Duration

**Requirement ID**: WF-011  
**Priority**: Medium

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start phase at 10:00 AM | Start time = 10:00 |
| 2 | Complete phase at 10:30 AM | End time = 10:30 |
| 3 | View phase details | Duration calculated = 30 minutes |
| 4 | Verify duration displayed in reports | Duration shows in analytics |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-WF-011: Phase Status Indicator on Dashboard

**Requirement ID**: DASH-003, DASH-004  
**Priority**: Medium

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as any operator | Dashboard displays |
| 2 | View batch list | Batches display with status badges |
| 3 | Verify color coding: | |
|  | - Pending = Grey | Correct color |
|  | - In Progress = Blue | Correct color |
|  | - Completed = Green | Correct color |
|  | - Failed = Red | Correct color |
| 4 | Verify real-time updates | Status changes without page refresh |

**Status**: ⃝ PASS  ⃝ FAIL

---

## 8. TEST CASES - QUALITY CONTROL

### TC-QC-001: Automatic Quarantine After Mixing

**Requirement ID**: QC-001, QC-002, QC-006  
**Priority**: Critical

**Objective**: Verify batch automatically enters quarantine after mixing phase for ointments.

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete Mixing phase for ointment batch | Mixing status = "Completed" |
| 2 | Verify quarantine record auto-created | Quarantine record exists for batch |
| 3 | Verify quarantine status = "In Quarantine" | Status correct |
| 4 | Verify quarantine_date = current timestamp | Timestamp recorded |
| 5 | Verify next phase (Tube Filling) = "Pending" | Next phase waiting for QC |
| 6 | Verify batch visible in QC dashboard | QC users can see quarantined batch |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-002: Automatic Quarantine After Blending (Tablets)

**Requirement ID**: QC-001, QC-002  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete Blending phase for tablet batch | Blending completed |
| 2 | Verify batch enters quarantine | Quarantine record created |
| 3 | Verify Compression phase blocked | Cannot start until QC approves |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-003: Automatic Quarantine After Compression

**Requirement ID**: QC-001  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete Compression phase for tablet batch | Compression completed |
| 2 | Verify batch enters quarantine | Second quarantine record created |
| 3 | Verify Sorting phase blocked | Cannot proceed until QC approval |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-004: Request Sample from Quarantine

**Requirement ID**: QC-008, QC-009, QC-010  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as production operator | Dashboard displays |
| 2 | View batch in quarantine | Quarantine status visible |
| 3 | Click "Request Sample" button | Sample request form displays |
| 4 | Enter sample request details | Form accepts input |
| 5 | Submit sample request | Request created, sample_number = 1 |
| 6 | Verify quarantine status = "Sample Requested" | Status updated |
| 7 | Verify sample_count incremented | Count = 1 |
| 8 | Verify QA notified | Notification sent to QA |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-005: Limit Sample Requests to Maximum 2

**Requirement ID**: QC-009  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Request first sample | Sample 1 created |
| 2 | QC fails first sample | Sample status = "Failed" |
| 3 | Request second sample | Sample 2 created |
| 4 | Verify can_request_sample property | Returns True (can request) |
| 5 | QC fails second sample | Sample status = "Failed" |
| 6 | Attempt to request third sample | Error: "Maximum 2 samples allowed" |
| 7 | Verify "Request Sample" button disabled | Button not clickable |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-006: QA Sample Collection

**Requirement ID**: QC-011  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as QA user (qa_test) | QA dashboard displays |
| 2 | Navigate to "Pending Samples" | Sample requests list displays |
| 3 | Select sample request | Request details display |
| 4 | Click "Collect Sample" button | Sample collection form displays |
| 5 | Enter sample details: | |
|  | - Sample ID: "SAMP-001" | Field accepts input |
|  | - Sample quantity: "100g" | Field accepts input |
|  | - Storage condition: "Room temp" | Field accepts input |
| 6 | Enter QA comments | Text area accepts input |
| 7 | Click "Forward to QC" | Sample status = "Sample with QC" |
| 8 | Verify sampled_by = qa_test | QA identity recorded |
| 9 | Verify sample_date = current timestamp | Timestamp recorded |
| 10 | Verify QC notified | Notification sent to QC |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-007: QC Testing and Approval

**Requirement ID**: QC-003, QC-004, QC-012  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as QC user (qc_test) | QC dashboard displays |
| 2 | Navigate to "Samples for Testing" | Samples from QA display |
| 3 | Select sample | Sample details display |
| 4 | Click "Receive Sample" button | Status = "Sample in QC" |
| 5 | Verify received_by = qc_test | QC analyst identity recorded |
| 6 | Click "Enter Test Results" | Test results form displays |
| 7 | Enter test parameters: | |
|  | - pH: "7.2" (Spec: 7.0-7.5) | Within specification |
|  | - Viscosity: "2500 cP" (Spec: 2000-3000) | Within specification |
|  | - Appearance: "White homogeneous" | Meets requirement |
| 8 | Select result: "Pass" | Pass option selected |
| 9 | Enter QC comments: "All tests passed" | Comments accepted |
| 10 | Provide electronic signature | Password prompt |
| 11 | Confirm approval | Sample status = "Approved" |
| 12 | Verify test_date = current timestamp | Timestamp recorded |
| 13 | Verify quarantine status = "Sample Approved" | Quarantine updated |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-008: QC Testing and Rejection

**Requirement ID**: QC-012, QC-014  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | QC receives sample for testing | Status = "Sample in QC" |
| 2 | Enter test results: | |
|  | - pH: "8.5" (Spec: 7.0-7.5) | OUT OF SPECIFICATION |
| 3 | Select result: "Fail" | Fail option selected |
| 4 | Enter failure reason: "pH out of specification" | Reason required and captured |
| 5 | Confirm rejection | Sample status = "Failed" |
| 6 | Verify quarantine status = "Sample Failed" | Status updated |
| 7 | Verify previous phase status reset to "Pending" | Phase rollback initiated |
| 8 | Verify batch can re-execute failed phase | Operator can restart phase |
| 9 | Verify rollback event logged | Audit trail contains rollback |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-009: Phase Rollback on QC Failure

**Requirement ID**: QC-014, QC-015, QC-016, QC-017  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Tablet batch completes Blending | Blending status = "Completed" |
| 2 | Batch enters quarantine | Quarantine created |
| 3 | QC tests sample and fails it | Sample failed |
| 4 | Verify Blending phase status = "Pending" | Phase reset for re-execution |
| 5 | Verify Blending phase execution record marked | Original execution marked as "rolled back" |
| 6 | Blending Operator re-executes phase | New execution record created |
| 7 | Verify corrective action recorded | Comments captured |
| 8 | Complete Blending again | New completion timestamp |
| 9 | Enter quarantine again | New quarantine for re-test |
| 10 | QC approves this time | Sample passes |
| 11 | Verify batch proceeds to Compression | Next phase unlocked |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-010: Release Batch from Quarantine

**Requirement ID**: QC-013  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as quarantine manager | Dashboard displays |
| 2 | View batch with approved sample | Quarantine status = "Sample Approved" |
| 3 | Click "Release to Next Phase" button | Confirmation dialog displays |
| 4 | Confirm release | Quarantine status = "Released to Next Phase" |
| 5 | Verify released_date = current timestamp | Timestamp recorded |
| 6 | Verify released_by = quarantine manager | Identity recorded |
| 7 | Verify next phase triggered | Next phase status = "Pending" (ready) |
| 8 | Verify batch no longer in quarantine list | Removed from active quarantine |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-QC-011: Quarantine Duration Calculation

**Requirement ID**: QC-013  
**Priority**: Medium

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Batch enters quarantine at 10:00 AM | Quarantine_date = 10:00 |
| 2 | Batch released at 2:00 PM same day | Released_date = 14:00 |
| 3 | View quarantine duration | Duration = 4.0 hours |
| 4 | Verify duration displayed in dashboard | Metric visible to managers |

**Status**: ⃝ PASS  ⃝ FAIL

---

## 9. TEST CASES - MATERIAL MANAGEMENT

### TC-MAT-001: Release Raw Materials

**Requirement ID**: MAT-001, MAT-002  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as store manager (store_mgr_test) | Store dashboard displays |
| 2 | Navigate to "Material Release" | BMR list displays |
| 3 | Select approved BMR | BMR details display |
| 4 | Click "Release Materials" button | Material release form displays |
| 5 | Enter material details: | |
|  | - Material: "Paracetamol API" | Dropdown selection |
|  | - Quantity: "25 kg" | Field accepts input |
|  | - Batch/Lot: "RAW-12345" | Field accepts input |
|  | - Expiry Date: "31-Dec-2027" | Date picker |
| 6 | Click "Release" button | Material released successfully |
| 7 | Verify release_date = current timestamp | Timestamp recorded |
| 8 | Verify released_by = store manager | Identity recorded |
| 9 | Verify material visible to Dispensing Manager | Material appears in dispensing queue |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-MAT-002: Dispense Materials to Production

**Requirement ID**: MAT-005, MAT-006  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as dispensing manager | Dispensing dashboard displays |
| 2 | View released materials | Materials from store manager display |
| 3 | Select material to dispense | Material details display |
| 4 | Enter dispensing details: | |
|  | - Actual weight: "24.95 kg" | Field accepts input |
|  | - Production line: "Line 1" | Dropdown selection |
|  | - Container ID: "CONT-001" | Field accepts input |
| 5 | Provide electronic signature | Password prompt |
| 6 | Confirm dispensing | Material dispensed successfully |
| 7 | Verify dispensing_date = current timestamp | Timestamp recorded |
| 8 | Verify dispensed_by = dispensing manager | Identity recorded |
| 9 | Verify material traceability maintained | Link from raw material to BMR intact |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-MAT-003: Material Yield Calculation

**Requirement ID**: MAT-007  
**Priority**: Medium

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Release 25.00 kg material | Theoretical = 25.00 kg |
| 2 | Dispense 24.95 kg actual | Actual = 24.95 kg |
| 3 | View yield calculation | Yield = 99.8% |
| 4 | Verify yield within acceptable range | Alert if <95% or >105% |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-MAT-004: Packaging Material Release

**Requirement ID**: MAT-008, MAT-009  
**Priority**: High

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as packaging store user | Packaging dashboard displays |
| 2 | Select BMR at Packaging Release phase | BMR details display |
| 3 | Click "Release Packaging Materials" | Packaging release form displays |
| 4 | Select packaging items: | |
|  | - Blister strips (1000 units) | Selected |
|  | - Cartons (100 units) | Selected |
|  | - Labels (1000 units) | Selected |
| 5 | Enter batch numbers for packaging | Fields accept input |
| 6 | Confirm release | Packaging materials released |
| 7 | Verify packaging_released flag = True | Flag set |
| 8 | Verify next phase (packing) unlocked | Packing phase ready |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-MAT-005: Material Traceability Report

**Requirement ID**: MAT-004  
**Priority**: High

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Reports → Material Traceability | Report page displays |
| 2 | Enter batch number: "001-2026" | Batch selected |
| 3 | Generate traceability report | Report generated |
| 4 | Verify report shows: | |
|  | - All raw materials used | Listed with batch/lot numbers |
|  | - Material release dates | Timestamps shown |
|  | - Dispensing records | Who dispensed, when, how much |
|  | - Packaging materials | Packaging batch numbers |
|  | - Finished goods batch | Final product batch number |
| 5 | Verify complete chain from raw material to FG | Full traceability established |
| 6 | Export report to PDF | PDF generated successfully |

**Status**: ⃝ PASS  ⃝ FAIL

---

## 10. TEST CASES - FINISHED GOODS

### TC-FGS-001: Auto-Create Finished Goods Inventory

**Requirement ID**: FGS-001, FGS-002  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete all production phases for batch | All phases status = "Completed" |
| 2 | Complete Final QA phase | Final QA completed |
| 3 | Verify FGS inventory record auto-created | FGS record exists |
| 4 | Verify FGS record contains: | |
|  | - Batch number | Correct batch number |
|  | - Product name | Correct product |
|  | - Quantity available | = Batch size from BMR |
|  | - Unit of measure | Correct unit |
|  | - Manufacturing date | From BMR |
|  | - Created_at timestamp | Current date/time |
| 5 | Verify initial status = "Stored" | Status correct |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-FGS-002: View Finished Goods Inventory

**Requirement ID**: FGS-003  
**Priority**: High

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as FGS user | FGS dashboard displays |
| 2 | Navigate to "Inventory" | FGS inventory list displays |
| 3 | Verify columns visible: | |
|  | - Batch number | Visible |
|  | - Product name | Visible |
|  | - Quantity available | Visible |
|  | - Manufacturing date | Visible |
|  | - Status | Visible |
| 4 | Apply filters (by product, date range) | Filter works correctly |
| 5 | Search by batch number | Search returns correct results |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-FGS-003: Release Finished Goods for Sale

**Requirement ID**: FGS-003, FGS-004  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as FGS user | Dashboard displays |
| 2 | Select inventory item | Item details display |
| 3 | Click "Release Product" button | Release form displays |
| 4 | Enter release details: | |
|  | - Release type: "Sale" | Dropdown selection |
|  | - Quantity: "10,000 tablets" | Field accepts input |
|  | - Customer name: "ABC Pharmacy" | Field accepts input |
|  | - Customer contact: "0700123456" | Field accepts input |
|  | - Delivery address: "Kampala, Uganda" | Text area accepts input |
|  | - Invoice number: "INV-2026-001" | Field accepts input |
|  | - Unit price: "50 UGX" | Field accepts input (optional) |
| 5 | System calculates total value | Total = Quantity × Unit price |
| 6 | Provide electronic signature | Password prompt |
| 7 | Confirm release | Release record created |
| 8 | Verify quantity_available reduced | Original - Released = New available |
| 9 | Verify release record in history | Release visible in releases table |
| 10 | Verify authorized_by = FGS user | User identity recorded |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-FGS-004: Prevent Over-Release

**Requirement ID**: FGS-003  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Inventory shows 10,000 tablets available | Quantity = 10,000 |
| 2 | Attempt to release 15,000 tablets | Validation error displays |
| 3 | Error message: "Cannot release more than available quantity" | Error shown |
| 4 | Release prevented | No release record created |
| 5 | Quantity_available unchanged | Still shows 10,000 |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-FGS-005: Update Inventory Status

**Requirement ID**: FGS-005  
**Priority**: High

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Select inventory item (status = "Stored") | Item details display |
| 2 | Click "Update Status" button | Status dropdown displays |
| 3 | Change status to "Available for Sale" | Status changed |
| 4 | Save changes | Status updated in database |
| 5 | Change status to "Reserved" | Status changed |
| 6 | Change status to "Recalled" | Status changed |
| 7 | Verify status history maintained | All status changes logged |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-FGS-006: Finished Goods Report

**Requirement ID**: REP-003  
**Priority**: Medium

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Reports → Finished Goods | Report page displays |
| 2 | Select date range: "Last 30 days" | Date range applied |
| 3 | Generate report | Report displays |
| 4 | Verify report shows: | |
|  | - Total batches produced | Count shown |
|  | - Total quantity in inventory | Sum calculated |
|  | - Total quantity released | Sum calculated |
|  | - Inventory value (if pricing enabled) | Value calculated |
| 5 | Export to Excel | Excel file downloaded |

**Status**: ⃝ PASS  ⃝ FAIL

---

## 11. TEST CASES - SECURITY AND AUDIT

### TC-SEC-001: Password Complexity Validation

**Requirement ID**: USER-002, SEC-001  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Attempt to create user with password: "123" | Error: "Password too short (min 8 characters)" |
| 2 | Attempt password: "abcdefgh" | Error: "Password must contain numbers" |
| 3 | Attempt password: "12345678" | Error: "Password must contain letters" |
| 4 | Use password: "Test@1234" | Password accepted |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-SEC-002: Audit Trail for BMR Creation

**Requirement ID**: REG-003, SEC-012  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as qa_test | Login recorded in audit trail |
| 2 | Create new BMR | BMR creation recorded |
| 3 | View audit trail for this BMR | Audit entry shows: |
|  | - User: qa_test | User identity correct |
|  | - Action: "BMR Created" | Action correct |
|  | - Timestamp | Current date/time |
|  | - BMR Number | Correct BMR reference |
|  | - Changes: All field values | Initial values recorded |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-SEC-003: Audit Trail for BMR Approval

**Requirement ID**: REG-003  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as reg_test | Login recorded |
| 2 | Approve BMR | Approval recorded in audit |
| 3 | View audit trail | Entry shows: |
|  | - User: reg_test | Correct user |
|  | - Action: "BMR Approved" | Correct action |
|  | - Timestamp | Current date/time |
|  | - Status change: Submitted → Approved | State transition recorded |
|  | - Comments | Approval comments captured |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-SEC-004: Audit Trail for Phase Execution

**Requirement ID**: REG-003, SEC-012  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Mixing Operator starts phase | Phase start recorded in audit |
| 2 | View audit trail | Entry shows: |
|  | - User: mix_op_test | Operator identity |
|  | - Action: "Phase Started - Mixing" | Action correct |
|  | - BMR/Batch reference | Correct batch |
|  | - Start timestamp | Time recorded |
| 3 | Operator completes phase | Phase completion recorded |
| 4 | View audit trail | Entry shows: |
|  | - Action: "Phase Completed - Mixing" | Action correct |
|  | - End timestamp | Time recorded |
|  | - Process parameters | All parameters logged |
|  | - Electronic signature | Signature recorded |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-SEC-005: Audit Trail Immutability

**Requirement ID**: SEC-013  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as admin | Admin dashboard displays |
| 2 | Attempt to access audit trail edit function | No edit function available |
| 3 | Verify database permissions | Audit table is INSERT-only (no UPDATE/DELETE) |
| 4 | Verify audit records cannot be modified | Records are read-only |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-SEC-006: HTTPS Encryption

**Requirement ID**: SEC-008  
**Priority**: Critical (for production)

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Access system via HTTPS URL | SSL certificate valid |
| 2 | Check browser security indicator | Lock icon displays |
| 3 | Verify certificate details | Certificate issued to correct domain |
| 4 | Attempt HTTP access | Redirects to HTTPS automatically |

**Status**: ⃝ PASS  ⃝ FAIL  ⃝ N/A (if test environment)

---

### TC-SEC-007: CSRF Protection

**Requirement ID**: SEC-009  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Inspect form HTML source | CSRF token present in form |
| 2 | Attempt to submit form without token | Request rejected: "CSRF verification failed" |
| 3 | Submit form with valid token | Form submitted successfully |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-SEC-008: Session Security

**Requirement ID**: SEC-003, SEC-004  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as user | Session created |
| 2 | Check session cookie properties | HttpOnly, Secure, SameSite flags set |
| 3 | Idle for 30 minutes | Session expires |
| 4 | Attempt action after timeout | Redirected to login |
| 5 | Login again | New session created |
| 6 | Verify old session invalidated | Old session ID no longer valid |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-SEC-009: Unauthorized Access Prevention

**Requirement ID**: SEC-005, SEC-006, SEC-007  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as Mixing Operator | Limited access granted |
| 2 | Attempt direct URL to Admin panel | Access denied, redirect to dashboard |
| 3 | Attempt direct URL to QA BMR creation | Access denied |
| 4 | Attempt API call without authentication | 401 Unauthorized response |
| 5 | Attempt API call with invalid token | 403 Forbidden response |
| 6 | Attempt SQL injection in form | Input sanitized, attack prevented |

**Status**: ⃝ PASS  ⃝ FAIL

---

### TC-SEC-010: Electronic Signature Verification

**Requirement ID**: USER-011, USER-012, USER-013  
**Priority**: Critical

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Complete phase requiring e-signature | Signature prompt displays |
| 2 | Verify prompt shows: | |
|  | - User full name | Displayed |
|  | - User role | Displayed |
|  | - Action being signed | Clear description |
|  | - Meaning of signature | "I certify this action is accurate" |
| 3 | Enter incorrect password | Error: "Invalid password" |
| 4 | Enter correct password | Signature accepted |
| 5 | View signed record | Shows: |
|  | - Signer name and role | Correct |
|  | - Timestamp with timezone | Recorded |
|  | - Action signed | Recorded |

**Status**: ⃝ PASS  ⃝ FAIL

---

## 12. TEST SUMMARY

### 12.1 Test Execution Summary

**To be completed after test execution:**

| Module | Total Tests | Passed | Failed | Blocked | N/A | Pass % |
|--------|-------------|--------|--------|---------|-----|--------|
| User Management | 15 | ___ | ___ | ___ | ___ | ___% |
| BMR Management | 25 | ___ | ___ | ___ | ___ | ___% |
| Workflow Engine | 30 | ___ | ___ | ___ | ___ | ___% |
| Quality Control | 20 | ___ | ___ | ___ | ___ | ___% |
| Material Management | 15 | ___ | ___ | ___ | ___ | ___% |
| Finished Goods | 12 | ___ | ___ | ___ | ___ | ___% |
| Dashboards | 10 | ___ | ___ | ___ | ___ | ___% |
| Reporting | 10 | ___ | ___ | ___ | ___ | ___% |
| Security & Audit | 15 | ___ | ___ | ___ | ___ | ___% |
| **TOTAL** | **152** | **___** | **___** | **___** | **___** | **___%** |

**Acceptance Criteria**: ≥95% pass rate required for OQ approval

### 12.2 Defect Summary

**To be completed during test execution:**

| Defect ID | Test Case | Severity | Description | Status |
|-----------|-----------|----------|-------------|--------|
| DEF-001 | | | | |
| DEF-002 | | | | |
| DEF-003 | | | | |

### 12.3 Test Completion Criteria

OQ is considered complete when:
- ✓ All test cases executed
- ✓ Pass rate ≥ 95%
- ✓ All critical defects resolved
- ✓ All high severity defects resolved or risk-accepted
- ✓ Test documentation reviewed and approved
- ✓ Deviations (if any) documented and closed

---

## 13. APPENDICES

### Appendix A: Test Data

**Test Users Login Credentials:**
(Store securely, do not include in final validation package)

| Username | Password | Role |
|----------|----------|------|
| admin_test | [REDACTED] | Admin |
| qa_test | [REDACTED] | Quality Assurance |
| reg_test | [REDACTED] | Regulatory Affairs |
| ... | ... | ... |

### Appendix B: Test Environment Configuration

**Server Details:**
- Hostname: [TO BE COMPLETED]
- IP Address: [TO BE COMPLETED]
- Operating System: [TO BE COMPLETED]
- Python Version: [TO BE COMPLETED]
- Django Version: [TO BE COMPLETED]

### Appendix C: Deviations Log

All test deviations must be documented using format:

**Deviation Number**: DEV-OQ-001  
**Test Case**: TC-XXX-001  
**Date Identified**: [DATE]  
**Description**: [Description of deviation]  
**Impact**: [High/Medium/Low]  
**Root Cause**: [Analysis]  
**Corrective Action**: [Action taken]  
**Re-test Required**: [Yes/No]  
**Status**: [Open/Closed]  

---

## APPROVAL SIGNATURES

**Test Execution:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Test Lead | _________________ | _________________ | __________ |
| Tester 1 | _________________ | _________________ | __________ |
| Tester 2 | _________________ | _________________ | __________ |

**Test Review & Approval:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| QA Manager | _________________ | _________________ | __________ |
| IT Manager | _________________ | _________________ | __________ |
| Validation Lead | _________________ | _________________ | __________ |

---

**Document Control**
- Test execution started: __________
- Test execution completed: __________
- Document Location: [Quality Management System / Validation Files]

---

**END OF OPERATIONAL QUALIFICATION PROTOCOL**
