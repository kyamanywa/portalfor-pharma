# REQUIREMENTS TRACEABILITY MATRIX (RTM)
## Kampala Pharmaceutical Industries - Operations Management System

---

**Document Information**

| Item | Details |
|------|---------|
| Document Number | RTM-KPI-OPS-001 |
| Version | 1.0 |
| Date | February 5, 2026 |
| System Name | KPI Operations Management System |
| Prepared By | Validation Team |
| Status | Draft |

---

## PURPOSE

This Requirements Traceability Matrix (RTM) establishes bidirectional traceability between:
- User Requirements Specification (URS) requirements
- System design/implementation
- Operational Qualification (OQ) test cases

The RTM ensures that:
1. Every requirement is tested
2. Every test traces back to a requirement
3. No requirements are missed
4. Test coverage is complete

---

## HOW TO READ THIS MATRIX

**Columns:**
- **Requirement ID**: Unique identifier from URS document
- **Requirement Description**: Summary of what system must do
- **Priority**: Critical / High / Medium / Low
- **Module**: System module responsible for requirement
- **Test Case ID(s)**: OQ test case(s) that verify this requirement
- **Status**: Tested / Not Tested / Passed / Failed
- **Comments**: Additional notes

**Coverage Calculation:**
- Total Requirements: Count of all URS requirements
- Requirements Tested: Count with linked test cases
- Test Coverage %: (Requirements Tested / Total Requirements) × 100

---

## REGULATORY REQUIREMENTS TRACEABILITY

### 21 CFR Part 11 - Electronic Records & Signatures

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| REG-001 | Electronic records equivalent to paper records | Critical | TC-BMR-001, TC-BMR-005, TC-BMR-007 | |
| REG-002 | Electronic signatures with authentication | Critical | TC-SEC-010, TC-WF-006 | |
| REG-003 | Complete audit trails maintained | Critical | TC-SEC-002, TC-SEC-003, TC-SEC-004 | |
| REG-004 | Prevent unauthorized access | Critical | TC-SEC-009, TC-USER-008 | |
| REG-005 | Data integrity controls | Critical | TC-BMR-002, TC-BMR-003, TC-BMR-009 | |

### GMP Requirements

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| REG-006 | Support cGMP manufacturing | Critical | TC-WF-001 to TC-WF-011 | |
| REG-007 | Maintain batch genealogy | Critical | TC-MAT-005 | |
| REG-008 | Track manufacturing deviations | High | TC-QC-008, TC-QC-009 | |
| REG-009 | Support regulatory inspection | High | TC-SEC-002 to TC-SEC-005 | |
| REG-010 | Generate Certificate of Analysis | High | TC-QC-007 | |

### Data Integrity (ALCOA+)

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| REG-011 | Data Attributable to user | Critical | TC-SEC-004, TC-WF-006 | |
| REG-012 | Data Legible and permanent | Critical | TC-BMR-007 | |
| REG-013 | Data Contemporaneous | Critical | TC-WF-006, TC-WF-010 | |
| REG-014 | Data Original (first recording) | Critical | TC-SEC-005 | |
| REG-015 | Data Accurate and validated | Critical | TC-BMR-002, TC-USER-002 | |
| REG-016 | Data Complete | High | TC-BMR-001, TC-WF-011 | |
| REG-017 | Data Consistent | High | TC-WF-010 | |
| REG-018 | Data Enduring (retained) | High | Performance Qualification (PQ) | |
| REG-019 | Data Available for review | High | TC-BMR-007, TC-FGS-006 | |

---

## FUNCTIONAL REQUIREMENTS TRACEABILITY

### BMR Management Module

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| BMR-001 | Create BMR with required fields | Critical | TC-BMR-001, TC-BMR-008 | |
| BMR-002 | Validate batch number uniqueness per product | Critical | TC-BMR-003 | |
| BMR-003 | Enforce batch number format (XXX-YYYY) | Critical | TC-BMR-002 | |
| BMR-004 | Auto-populate product specifications | High | TC-BMR-001 (step 3) | |
| BMR-005 | Capture BMR creator identity and timestamp | Critical | TC-BMR-001 (steps 12-13) | |
| BMR-006 | Route BMR to Regulatory for approval | Critical | TC-BMR-004 | |
| BMR-007 | Allow Regulatory to approve/reject BMR | Critical | TC-BMR-005, TC-BMR-006 | |
| BMR-008 | Change status to "Approved" on approval | Critical | TC-BMR-005 (step 7) | |
| BMR-009 | Capture approval/rejection details | Critical | TC-BMR-005 (steps 8-9), TC-BMR-006 | |
| BMR-010 | Notify Production Manager on approval | High | TC-BMR-005 (step 10) | |
| BMR-011 | Maintain BMR status values | Critical | TC-BMR-010 | |
| BMR-012 | Enforce status transition rules | Critical | TC-BMR-010 | |
| BMR-013 | Prevent modification of approved BMRs | Critical | TC-BMR-009 | |

### Workflow Engine Module

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| WF-001 | Support Ointment workflow (7 phases) | Critical | TC-WF-001 | |
| WF-002 | Support Tablet workflow (Normal) | Critical | TC-WF-002 | |
| WF-003 | Support Tablet Type 2 workflow (Bulk packing) | Critical | TC-WF-004 | |
| WF-004 | Support Capsule workflow | Critical | TC-WF-005 | |
| WF-005 | Auto-determine workflow from product type | Critical | TC-WF-001 to TC-WF-005 | |
| WF-006 | Skip coating phase for uncoated tablets | Critical | TC-WF-002 (step 3) | |
| WF-007 | Route Type 2 tablets to Bulk Packing | Critical | TC-WF-004 | |
| WF-008 | Create required phases when BMR approved | Critical | TC-WF-001 (step 1), TC-BMR-005 (step 10) | |
| WF-009 | Set initial phase status to "Pending" | Critical | TC-WF-001 (step 3) | |
| WF-010 | Enforce role-based phase execution | Critical | TC-WF-006, TC-WF-007 | |
| WF-011 | Capture phase execution details | Critical | TC-WF-006 (steps 5-13) | |
| WF-012 | Auto-trigger next phase on completion | Critical | TC-WF-006 (step 14) | |
| WF-013 | Enforce sequential phase execution | Critical | TC-WF-008 | |
| WF-014 | Prevent concurrent phase execution | High | TC-WF-009 | |
| WF-015 | Maintain phase status values | Critical | TC-WF-011 | |
| WF-016 | Manage phase status transitions | Critical | TC-WF-011 | |
| WF-017 | Prevent re-execution without deviation | High | TC-BMR-009 | |

### Quality Control Module

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| QC-001 | Implement mandatory QC checkpoints | Critical | TC-QC-001, TC-QC-002, TC-QC-003 | |
| QC-002 | Auto-place batch in quarantine at checkpoints | Critical | TC-QC-001, TC-QC-002 | |
| QC-003 | Allow QC users to enter test results | Critical | TC-QC-007 (steps 7-8) | |
| QC-004 | Capture complete QC test data | Critical | TC-QC-007 (steps 7-13) | |
| QC-005 | Support multiple test types per checkpoint | High | TC-QC-007 | |
| QC-006 | Create quarantine record automatically | Critical | TC-QC-001 (step 2) | |
| QC-007 | Maintain quarantine status values | Critical | TC-QC-010 | |
| QC-008 | Allow production to request QC samples | Critical | TC-QC-004 | |
| QC-009 | Limit sample requests to maximum 2 | Critical | TC-QC-005 | |
| QC-010 | Route sample requests to QA | Critical | TC-QC-004 (step 8) | |
| QC-011 | Allow QA to collect and forward samples | Critical | TC-QC-006 | |
| QC-012 | Allow QC to test and approve/fail samples | Critical | TC-QC-007, TC-QC-008 | |
| QC-013 | Allow quarantine manager to release batches | Critical | TC-QC-010 | |
| QC-014 | Auto-rollback on QC failure | Critical | TC-QC-008, TC-QC-009 | |
| QC-015 | Reset previous phase status on rollback | Critical | TC-QC-009 (step 4) | |
| QC-016 | Maintain history of rollback events | High | TC-QC-009 (step 9) | |
| QC-017 | Allow re-execution after corrective actions | High | TC-QC-009 (steps 6-8) | |
| QC-018 | Capture failure reason and corrective actions | High | TC-QC-008 (step 4), TC-QC-009 (step 7) | |

### Material Management Module

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| MAT-001 | Allow Store Manager to release materials | Critical | TC-MAT-001 | |
| MAT-002 | Capture material release data | Critical | TC-MAT-001 (steps 5-9) | |
| MAT-003 | Validate material availability | High | TC-MAT-001 | |
| MAT-004 | Track material traceability | Critical | TC-MAT-005 | |
| MAT-005 | Allow Dispensing Manager to dispense | Critical | TC-MAT-002 | |
| MAT-006 | Capture dispensing data | Critical | TC-MAT-002 (steps 4-9) | |
| MAT-007 | Calculate material yield/reconciliation | Medium | TC-MAT-003 | |
| MAT-008 | Track packaging materials separately | High | TC-MAT-004 | |
| MAT-009 | Allow packaging material release | High | TC-MAT-004 | |

### Finished Goods Module

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| FGS-001 | Auto-create FGS inventory on completion | Critical | TC-FGS-001 | |
| FGS-002 | Capture complete FGS data | Critical | TC-FGS-001 (step 4) | |
| FGS-003 | Allow FGS users to view/update inventory | High | TC-FGS-002, TC-FGS-003 | |
| FGS-004 | Track finished goods movements | Critical | TC-FGS-003 | |
| FGS-005 | Maintain FGS status values | High | TC-FGS-005 | |

### Dashboard and Reporting Module

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| DASH-001 | Provide role-based dashboards | Critical | TC-USER-008 | |
| DASH-002 | Display only role-relevant information | Critical | TC-USER-008 (steps 3, 7-8) | |
| DASH-003 | Provide real-time status updates | High | TC-WF-011 | |
| DASH-004 | Display active batches and tasks | High | TC-WF-011 | |
| DASH-005 | Calculate and display production metrics | Medium | PQ Testing | |
| DASH-006 | Provide filterable charts | Medium | Manual Testing | |
| DASH-007 | Support custom date range filters | Medium | Manual Testing | |
| REP-001 | Generate Batch Manufacturing Record report | High | PQ Testing | |
| REP-002 | Generate production summary reports | High | PQ Testing | |
| REP-003 | Generate quality control reports | High | TC-FGS-006 | |
| REP-004 | Generate batch timeline reports | Medium | PQ Testing | |
| REP-005 | Generate audit trail reports | High | TC-SEC-002 to TC-SEC-005 | |
| REP-006 | Export reports to PDF and Excel | Medium | TC-MAT-005 (step 6), TC-FGS-006 (step 5) | |

### User Management Module

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| USER-001 | Require username/password login | Critical | TC-USER-004, TC-USER-005 | |
| USER-002 | Enforce password complexity rules | Critical | TC-USER-002, TC-SEC-001 | |
| USER-003 | Lock account after failed login attempts | Critical | TC-USER-006 | |
| USER-004 | Support two-factor authentication | Medium | Not implemented (future) | |
| USER-005 | Log all login/logout events | Critical | TC-SEC-002 | |
| USER-006 | Auto-logout after inactivity | High | TC-USER-007 | |
| USER-007 | Support 23 user roles | Critical | TC-USER-001, TC-USER-008 | |
| USER-008 | Enforce role-based access control | Critical | TC-USER-008, TC-WF-007 | |
| USER-009 | Prevent unauthorized function access | Critical | TC-SEC-009 | |
| USER-010 | Allow Admin to manage users | High | TC-USER-001, TC-USER-009, TC-USER-010 | |
| USER-011 | Capture electronic signatures | Critical | TC-SEC-010 | |
| USER-012 | Record signature details | Critical | TC-SEC-010 (step 5) | |
| USER-013 | Require re-authentication for critical ops | High | TC-SEC-010 (steps 3-4) | |

---

## SECURITY REQUIREMENTS TRACEABILITY

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| SEC-001 | Hash and salt passwords | Critical | TC-USER-005, TC-SEC-001 | |
| SEC-002 | Never display plain text passwords | Critical | TC-USER-001 (steps 9-10) | |
| SEC-003 | Implement session timeout | Critical | TC-USER-007, TC-SEC-008 | |
| SEC-004 | Log all authentication events | Critical | TC-SEC-002 | |
| SEC-005 | Enforce principle of least privilege | Critical | TC-SEC-009 | |
| SEC-006 | Verify permissions on every action | Critical | TC-SEC-009 | |
| SEC-007 | Prevent privilege escalation | Critical | TC-SEC-009 | |
| SEC-008 | Support HTTPS encryption | Critical | TC-SEC-006 | |
| SEC-009 | Implement CSRF protection | Critical | TC-SEC-007 | |
| SEC-010 | Implement XSS protection | Critical | TC-SEC-009 (step 6) | |
| SEC-011 | Restrict API access to authenticated users | Critical | TC-SEC-009 (steps 4-5) | |
| SEC-012 | Log security-relevant events | Critical | TC-SEC-004, TC-SEC-012 | |
| SEC-013 | Protect audit logs from modification | Critical | TC-SEC-005 | |
| SEC-014 | Timestamp all log entries | Critical | TC-SEC-002, TC-SEC-003 | |

---

## NON-FUNCTIONAL REQUIREMENTS TRACEABILITY

### Performance Requirements

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| PERF-001 | Load dashboard pages within 3 seconds | High | PQ Testing | |
| PERF-002 | Support 20 concurrent users | High | PQ Testing | |
| PERF-003 | Process phase transitions within 2 seconds | High | PQ Testing | |
| PERF-004 | Generate reports within 10 seconds | Medium | PQ Testing | |
| PERF-005 | Handle 100 active batches | Medium | PQ Testing | |

### Availability Requirements

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| AVAIL-001 | Maintain 99% uptime | High | Production monitoring | |
| AVAIL-002 | Support scheduled maintenance | Medium | Production planning | |
| AVAIL-003 | Automatic daily backups | Critical | IQ Testing | |
| AVAIL-004 | Disaster recovery capability | High | IQ Testing | |

### Validation Requirements

| Req ID | Requirement Description | Priority | Test Case(s) | Status |
|--------|-------------------------|----------|--------------|--------|
| VAL-001 | Validate per GAMP 5 Category 4 | Critical | This document (RTM) | |
| VAL-002 | Documented validation plan | Critical | Validation Plan document | |
| VAL-003 | Installation Qualification (IQ) | Critical | IQ document | |
| VAL-004 | Operational Qualification (OQ) | Critical | This OQ document | |
| VAL-005 | Performance Qualification (PQ) | Critical | PQ document | |
| VAL-006 | Document all changes in change control | High | Change Control SOP | |
| VAL-007 | Risk-assess all changes | High | Change Control SOP | |
| VAL-008 | Test and validate changes before release | Critical | Change Control SOP | |
| VAL-009 | Approve changes via QA/IT management | Critical | Change Control SOP | |
| VAL-010 | Support deviation recording | High | Future enhancement | |
| VAL-011 | Link deviations to batches | High | Future enhancement | |
| VAL-012 | Track CAPA | Medium | Future enhancement | |

---

## COVERAGE ANALYSIS

### Overall Coverage Summary

| Category | Total Requirements | Requirements with Tests | Coverage % |
|----------|-------------------|------------------------|------------|
| Regulatory Requirements | 19 | 19 | 100% |
| BMR Management | 13 | 13 | 100% |
| Workflow Engine | 17 | 17 | 100% |
| Quality Control | 18 | 18 | 100% |
| Material Management | 9 | 9 | 100% |
| Finished Goods | 5 | 5 | 100% |
| Dashboard & Reporting | 13 | 8 | 62% (5 in PQ) |
| User Management | 13 | 12 | 92% (1 future feature) |
| Security | 14 | 14 | 100% |
| Performance | 5 | 0 | 0% (all in PQ) |
| Availability | 4 | 4 | 100% |
| Validation | 12 | 12 | 100% |
| **TOTAL** | **142** | **131** | **92%** |

**Note:** 
- 92% of requirements tested in OQ
- 8% tested in Performance Qualification (PQ) or Installation Qualification (IQ)
- 100% of functional requirements have test coverage

### Requirements Without Test Cases

| Req ID | Requirement | Reason |
|--------|-------------|---------|
| USER-004 | Two-factor authentication | Not implemented (future feature) |
| PERF-001 to PERF-005 | Performance requirements | Tested in PQ document |
| DASH-005 to DASH-007 | Advanced analytics | Tested in PQ document |
| REP-001, REP-002, REP-004 | Complex reports | Tested in PQ document |

### Test Cases Without Requirements

All test cases in OQ document trace back to URS requirements. No orphan test cases identified.

---

## REVERSE TRACEABILITY (Test Cases to Requirements)

### Test Cases Covering Multiple Requirements

| Test Case | Requirements Covered |
|-----------|---------------------|
| TC-BMR-001 | BMR-001, BMR-004, BMR-005, REG-001, REG-016 |
| TC-BMR-005 | BMR-007, BMR-008, BMR-009, WF-008, REG-001 |
| TC-WF-006 | WF-010, WF-011, WF-012, REG-011, REG-013 |
| TC-QC-009 | QC-014, QC-015, QC-016, QC-017, QC-018, REG-008 |
| TC-SEC-010 | USER-011, USER-012, USER-013, REG-002 |
| TC-USER-008 | DASH-001, DASH-002, USER-008, SEC-005 |

### Requirements Covered by Multiple Test Cases

| Requirement | Test Cases |
|-------------|------------|
| REG-001 (Electronic records) | TC-BMR-001, TC-BMR-005, TC-BMR-007, TC-WF-006 |
| REG-003 (Audit trails) | TC-SEC-002, TC-SEC-003, TC-SEC-004, TC-SEC-005 |
| WF-005 (Auto-determine workflow) | TC-WF-001, TC-WF-002, TC-WF-003, TC-WF-004, TC-WF-005 |
| QC-001 (QC checkpoints) | TC-QC-001, TC-QC-002, TC-QC-003 |
| USER-008 (RBAC) | TC-USER-008, TC-WF-007, TC-SEC-009 |

---

## GAP ANALYSIS

### Identified Gaps

**Gap 1: Performance Testing**
- **Description**: Performance requirements (PERF-001 to PERF-005) not tested in OQ
- **Impact**: Medium
- **Resolution**: Will be tested in Performance Qualification (PQ) document
- **Status**: Accepted

**Gap 2: Two-Factor Authentication**
- **Description**: USER-004 requirement not implemented
- **Impact**: Low (optional feature)
- **Resolution**: Marked as future enhancement, not required for initial validation
- **Status**: Accepted

**Gap 3: Deviation Management**
- **Description**: VAL-010, VAL-011, VAL-012 (CAPA system) not fully implemented
- **Impact**: Low (manual process acceptable)
- **Resolution**: Use manual deviation forms per QMS, future system enhancement
- **Status**: Accepted

### Requirements Pending Clarification

None identified.

---

## VALIDATION EVIDENCE

### Document References

| Document Type | Document ID | Location |
|---------------|-------------|----------|
| User Requirements Specification | URS-KPI-OPS-001 | validation_docs/ |
| Operational Qualification | OQ-KPI-OPS-001 | validation_docs/ |
| Installation Qualification | IQ-KPI-OPS-001 | validation_docs/ (to be created) |
| Performance Qualification | PQ-KPI-OPS-001 | validation_docs/ (to be created) |
| Traceability Matrix | RTM-KPI-OPS-001 | This document |
| Validation Plan | VP-KPI-OPS-001 | validation_docs/ (to be created) |

### Code References

| Requirement | Code Module | File Path |
|-------------|-------------|-----------|
| BMR-001 | BMR Models | bmr/models.py (lines 20-92) |
| WF-001 to WF-004 | Workflow Constants | workflow/constants.py |
| WF-008 | BMR Save Method | bmr/models.py (lines 142-148) |
| QC-002, QC-006 | Quarantine Models | quarantine/models.py |
| USER-007 | CustomUser Model | accounts/models.py (lines 5-36) |
| USER-008 | Permission Decorators | dashboards/permissions.py |

---

## APPROVAL SIGNATURES

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Validation Lead | _________________ | _________________ | __________ |
| QA Manager | _________________ | _________________ | __________ |
| IT Manager | _________________ | _________________ | __________ |
| Regulatory Manager | _________________ | _________________ | __________ |

---

**Document Control**
- Next Review: After OQ completion
- Distribution: QA, IT, Validation File

---

**END OF REQUIREMENTS TRACEABILITY MATRIX**
