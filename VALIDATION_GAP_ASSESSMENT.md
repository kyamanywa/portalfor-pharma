# KPI Operations Management System
## Technical Validation Gap Assessment

**Date:** 7 September 2026  
**Assessment type:** Static technical review and automated verification  
**Status:** Preliminary; not a QA release or regulatory certification

## 1. Scope assessed

The following controls were assessed:

1. Unique electronic-signature identity and re-authentication
2. Signature meaning, signer, date/time and record linkage
3. Prevention of unauthorized alteration or deletion
4. Secure audit trail with old and new values
5. Backup restoration and retention
6. Time synchronization and timezone control
7. Periodic access review and account deactivation
8. Controlled change management and release approval
9. Export, printed-record and PDF validation

## 2. Results summary

| Control | Evidence found | Result | Required follow-up |
|---|---|---|---|
| Signature identity | BMR signatures link to `signed_by`; QMS signatures link to a signer | Partial pass | Verify unique user identity and prevent shared accounts |
| Re-authentication | Existing signing paths use the active authenticated session; no consistent password re-entry was found | Fail / gap | Add controlled re-authentication to defined critical signing actions |
| Signature meaning and linkage | BMR signature type, user, date and BMR link exist; QMS signature meaning, target record and IP address exist | Partial pass | Test every critical signature route and record meaning consistently |
| Unauthorized change prevention | Login, role checks, status gates and foreign keys exist | Partial pass | Test direct URL access, POST tampering, deletion and approved-record edits |
| Audit old/new values | QMS activity and field-audit models store old/new values | Partial pass | Confirm all critical BMR and workflow changes are logged, protected and reviewable |
| Backup/restore | No executable backup/restore evidence exists in the application | Not demonstrated | IT must execute and document backup, restore and retention tests |
| Time control | Django timezone utilities are used and timezone settings exist | Partial pass | Verify host clock, database clock, timezone and DST/UTC behavior |
| Access review/deactivation | `is_active` and session tracking exist | Partial pass | Add or document periodic access-review procedure and evidence |
| Change control | QMS change-control models and approval signatures exist | Partial pass | Test segregation, approval, implementation, closure and effectiveness |
| PDF/export | PDF, CSV and Excel export paths exist | Partial pass | Compare exports to source records and verify completeness, pagination and metadata |

## 3. Automated verification performed

### Passed

- `python manage.py check`
- Product-route resolver verification:
  - normal capsule → `blister_packing`
  - UG capsule → `bulk_packing`
  - normal tablet → `blister_packing`
  - tablet type 2 → `bulk_packing`

### Blocked

- Dashboard/QMS test suite could not complete because a migration prints a Unicode check-mark character that cannot be encoded by the Windows `cp1252` console.
- Security test script could not complete because the system Python environment does not have the optional `axes` package installed.

These blocked tests are validation deviations and must not be recorded as passes.

## 4. Important implementation observations

### 4.1 Electronic signatures

The system stores several useful fields, including signer identity, signature type/meaning, timestamp, target record and sometimes IP address. However, a typed name or an existing login session is not by itself equivalent to validated electronic-signature re-authentication. The re-authentication requirement must be applied to a specifically approved list of critical actions and tested without changing ordinary data-entry behavior.

### 4.2 Audit trail coverage

QMS activity and field-audit records are designed to store the user, timestamp, IP address, field, old value and new value. This does not automatically prove that every BMR JSON field, workflow transition or deletion is captured. Coverage must be tested by changing representative records and reviewing the audit output.

### 4.3 Backup and retention

Backup and restore are operational IT controls, not merely Django features. The evidence must include backup location, encryption, schedule, retention period, restore timing, restored-record comparison and responsible personnel.

### 4.4 Exports and PDFs

The application has PDF, CSV and Excel paths. Validation must compare the generated output with the source record, including product, batch, phase, signatures, dates, page count, print layout, file naming and controlled-record metadata.

## 5. Safe remediation sequence

The following sequence preserves existing production flow:

1. Approve the critical-signature action list.
2. Add re-authentication only to those actions, using a dedicated confirmation step.
3. Add automated tests for valid password, invalid password, inactive user and unauthorized role.
4. Extend audit capture only where critical records currently lack old/new values.
5. Correct the Windows UTF-8 logging/migration issue.
6. Install and test approved security dependencies in the validation environment.
7. Execute backup/restore, access review, time-control and export tests.
8. Record deviations and retest.
9. Obtain QA, IT and Validation approval.

## 6. Release decision

Based on this assessment, the system is **not yet ready for a final compliance claim** for all nine controls. It is suitable for controlled remediation and formal IQ/OQ/PQ execution. No production workflow was changed as part of this assessment.

## 7. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| QA Manager |  |  |  |
| IT Manager |  |  |  |
| Validation Lead |  |  |  |

