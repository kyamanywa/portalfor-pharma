# KPI Operations Management System
## System Capability and Standards Review Dossier

**Document number:** KPI-SYS-STD-001  
**Version:** 1.0  
**Review date:** 7 September 2026  
**System owner:** Kampala Pharmaceutical Industries  
**Document status:** Draft for QA, IT and Regulatory review  

> This dossier describes the capabilities visible in the application source code and configuration. It is not, by itself, proof of GMP, 21 CFR Part 11, EU GMP Annex 11 or any other regulatory compliance. Compliance claims require approved procedures, validated infrastructure, executed tests, training records, signed deviations and QA release.

## 1. Executive summary

The KPI Operations Management System is a Django web application for electronic batch manufacturing records, production workflow control, quality activities, material traceability, finished-goods control, maintenance breakdowns and quality-system records.

The system supports three main manufacturing families:

| Product family | Variant | Intended packing route |
|---|---|---|
| Tablet | Normal | Blister packing |
| Tablet | Type 2 | Bulk packing |
| Capsule | Normal | Blister packing |
| Capsule | UG | Bulk packing |
| Ointment | Not variant-specific | Tube filling and secondary packaging |

The core application is functionally broad. However, the repository itself shows that formal validation execution is still required. The system should therefore be presented for standards review as **implemented software pending controlled validation**, not as automatically compliant software.

## 2. Scope

### Included

- User authentication, roles and dashboards
- BMR creation, approval, production and closure
- Product-specific workflow phases
- Material release and dispensing
- Manufacturing and packaging records
- Line clearance and QA signing gates
- QC checkpoints, quarantine and release decisions
- Finished-goods storage and release records
- Maintenance breakdown recording and notifications
- QMS records including documents, deviations, CAPA, audits, risks, calibration and training
- Reports, analytics, notifications and activity tracking

### Not established by this document

- Regulatory approval of the software
- Validation of the production installation
- Proof that every configured workflow is correct for every product
- Proof that backups, disaster recovery, access reviews or electronic signatures meet company SOPs
- Proof of performance under the intended production load

## 3. Technical architecture

| Area | Implemented capability | Review status |
|---|---|---|
| Application | Django web application with separate accounts, BMR, workflow, dashboards, products, reports, quarantine and finished-goods modules | Implemented |
| Database | Django ORM with migrations; SQLite exists for development/testing | Implemented; production database must be approved |
| API | Django REST Framework components are present | Requires endpoint inventory and OQ testing |
| Real-time updates | Django Channels, WebSocket consumers and notification signals are present | Requires operational test |
| Front end | Server-rendered HTML templates, JavaScript and responsive styles | Implemented; usability requires PQ |
| Deployment | WSGI/ASGI configuration and deployment scripts are present | IQ required |
| Reporting | Production, quality, timeline, BMR, quarantine and finished-goods reports are present | Requires report verification |
| Configuration | Database-backed workflow, dashboard and quality settings | Requires change-control procedure |

## 4. Capability register

| Capability | What the software can do | Evidence area | Status for standards review |
|---|---|---|---|
| Product master | Stores products, product type, tablet type, capsule type, batch-size data and specifications | `products/models.py` | Implemented; master-data governance required |
| BMR creation | Creates electronic batch records linked to a product and template | `bmr/models.py`, `bmr/views.py` | Implemented |
| BMR approval | Routes records for regulatory/QA review and records approval decisions | `dashboards/views.py`, `workflow/services.py` | Implemented; test all rejection paths |
| Batch numbering | Validates the configured batch-number format and product uniqueness rules | `bmr/models.py` | Implemented; confirm business format |
| BMR templates | Supports product-specific, product-type and universal template selection | `bmr/models.py` | Implemented; template governance required |
| Production workflow | Creates phase executions, statuses, ordering and next-phase activation | `workflow/services.py`, `workflow/models.py` | Implemented; OQ required |
| Tablet blister/bulk split | Normal tablet and type-2 tablet use different packing templates | `workflow/services.py`, workflow templates | Implemented |
| Capsule blister/bulk split | Normal capsule uses blister; UG capsule uses bulk | `workflow/services.py`, `workflow/utils.py` | Corrected; migration and OQ required |
| Ointment workflow | Supports mixing, QC, tube filling, secondary packaging and final QA | Workflow templates | Implemented |
| Line clearance | Supports operator completion, supervisor signing and QA approval gates | `BatchPhaseExecution` fields and phase views | Implemented; test unauthorized transitions |
| Process signing | Supports operator submission followed by QA signing for selected phases | `BatchPhaseExecution` fields and phase views | Implemented; signature validation required |
| Manufacturing data | Captures phase-specific data, comments, machine use, dates and shifts | BMR templates and phase views | Implemented; verify completeness and immutability |
| QC checkpoints | Supports pass/fail results, approvals, rejection reasons and rollback targets | `workflow/services.py`, QC dashboards | Implemented; OQ required |
| Quarantine | Places material/batches in quarantine and supports sample/release/reject workflows | `quarantine/`, workflow services | Implemented; end-to-end PQ required |
| Material traceability | Tracks material release, dispensing and packaging-material release | BMR and workflow modules | Implemented; reconcile against physical stores |
| Packaging records | Supports blister packing, bulk packing, secondary packaging and IPC records | `dashboards/bmr_form_views.py`, packing templates | Implemented; product-route tests required |
| QA handoff | Sends operator-completed sections to QA dashboards for review/signing | QA dashboard and phase views | Implemented; test with each product route |
| Finished goods | Supports finished-goods storage and release records | `fgs_management/` | Implemented; release authorization requires testing |
| Breakdown management | Records breakdown occurrence, start/end, reason, machine and duration | `BatchPhaseExecution`, maintenance dashboard | Implemented; maintenance workflow requires PQ |
| Maintenance notifications | Notifies maintenance roles of machine stage/product impact | workflow signals and maintenance dashboard | Implemented; notification delivery requires test |
| QMS documents | Records controlled documents, versions, review/signature and status | `dashboards/models.py`, QMS views | Implemented; document-control SOP required |
| Deviations | Records deviation type, impact, root cause, QA decision and closure | QMS models/views | Implemented; workflow approval tests required |
| CAPA | Creates corrective/preventive actions, owners, due dates and effectiveness information | QMS models/views | Implemented; effectiveness verification required |
| Change control | Records changes and related QMS actions | QMS models/views | Implemented; verify approval segregation |
| Audits and risks | Records audits, observations, corrective actions and risk assessments | QMS models/views | Implemented; review scoring model |
| Calibration | Records equipment calibration and due dates | QMS calibration models and alerts | Implemented; verify alert scheduling |
| Training | Records training assignment/status and links to controlled documents | QMS training models | Implemented; verify qualification rules |
| Notifications | Supports dashboard, database and real-time notification mechanisms | dashboards and workflow signals | Implemented; delivery and acknowledgement require testing |
| Analytics | Provides production, quality, timing, equipment and inventory summaries | `dashboards/analytics.py` | Implemented; reconcile calculations |
| Audit/activity records | Stores user sessions, workflow events and QMS activity records | accounts, workflow and dashboards models | Present; audit-trail completeness must be demonstrated |

## 5. End-to-end workflow descriptions

### 5.1 BMR lifecycle

1. QA or an authorized user selects the product and template.
2. The BMR records product, batch, manufacturing and expiry details.
3. The record is submitted for approval.
4. Regulatory/QA approval or rejection is recorded.
5. The workflow engine creates phase executions based on the product route.
6. Authorized departments complete phases in sequence.
7. Required QA/QC gates control progression.
8. Completed batches proceed through final QA and finished-goods storage.

### 5.2 Product-route rules

The product route must be selected before BMR workflow creation and must not be changed casually after phase executions exist.

| Product data | Workflow template | Packing phase |
|---|---|---|
| `product_type=tablet`, normal | `tablet` | `blister_packing` |
| `product_type=tablet`, `tablet_type=tablet_2` | `tablet_type_2` | `bulk_packing` |
| `product_type=capsule`, `capsule_type=normal` | `capsule` | `blister_packing` |
| `product_type=capsule`, `capsule_type=ug` | `capsule_ug` | `bulk_packing` |

If a product type or variant is changed after a BMR is created, the existing phase executions do not automatically become a new workflow. The approved operational rule should be to correct the product before workflow initialization or process the change through a controlled, authorized rework/recreation procedure.

## 6. Roles and access model

The user model includes the following functional roles:

| Group | Roles |
|---|---|
| Administration | Admin |
| Quality | Head QA, QA, QC, Quarantine Manager |
| Regulatory | Regulatory |
| Production management | Production Manager |
| Materials | Store Manager, Dispensing Manager, Packaging Store |
| Finished goods | Finished Goods Store |
| Operations | Mixing, tube-filling, granulation, blending, compression, coating, filling, sorting, packing and dispensing operators |
| Equipment | Equipment Operator, Maintenance Technician |
| Support | Cleaning Operator |

Access is implemented through Django authentication, role checks, dashboard permissions and staff/superuser controls. QA must approve a role-permission matrix and verify least privilege, segregation of duties, inactive-user handling and periodic access review.

## 7. Data integrity and electronic records

The application contains controls that support data integrity:

- User-attributed records and workflow actions
- Timestamped approvals and phase execution data
- Database constraints and foreign-key relationships
- Status-controlled workflow progression
- Role-restricted dashboards and actions
- Line-clearance and process-signing statuses
- QMS activity and field-audit records
- User session tracking
- Migration-controlled schema changes

The following must be demonstrated before making a formal ALCOA+ or Part 11 claim:

- Unique electronic-signature identity and re-authentication at signing
- Signature meaning, signer name, date/time and record linkage
- Prevention of unauthorized alteration or deletion
- Secure, reviewable audit trail containing old and new values where required
- Backup restoration and retention
- Time synchronization and timezone control
- Periodic access review and account deactivation
- Controlled change management and release approval
- Validation of exports, printed records and PDF output

## 8. Security and operational controls

Implemented or configured areas include authentication, role-based access, session timeout/security settings, user sessions, Django CSRF protection, password handling through Django and optional OTP-related middleware/configuration.

Before production release, IT must verify:

- Production uses a supported database rather than development SQLite.
- Secrets are externalized and not stored in source control.
- HTTPS is enforced.
- Debug mode is disabled.
- Backups are encrypted, tested and monitored.
- Logs are retained, protected and reviewed.
- Security patches are controlled.
- Superuser access is restricted and reviewed.
- Disaster recovery and business continuity procedures are tested.

## 9. Validation and standards position

The repository contains URS, OQ and traceability drafts, but document existence is not test execution. The following evidence is required for a defensible release package:

| Validation deliverable | Required evidence | Current position |
|---|---|---|
| User Requirements Specification | Approved requirements and signatures | Draft package exists; approval required |
| Risk assessment | Criticality, patient/product/data risks and controls | Must be approved |
| Installation Qualification | Environment, versions, installation and configuration evidence | Must be executed |
| Operational Qualification | Signed test results for roles, workflows, calculations, security and error handling | Must be executed |
| Performance Qualification | Representative production scenarios and trained users | Must be executed |
| Traceability matrix | Requirement-to-test-to-result links | Draft exists; update with actual results |
| Deviation management | Defects, impact assessment, CAPA and retest evidence | Required during testing |
| Validation summary report | Final pass/fail decision and QA release | Not complete until testing closes |
| SOP package | Operation, access, backup, incident, change and review procedures | Required |
| Training records | Evidence that users are trained before use | Required |

The software can support controls associated with GMP, ALCOA+, 21 CFR Part 11 and EU GMP Annex 11, but those standards cannot be claimed solely because a feature exists in code.

## 10. Known limitations and controls

| Risk/limitation | Impact | Required control |
|---|---|---|
| Editing product type after BMR workflow creation can leave stale phase executions | Wrong production/packing route and QA handoff | Lock route-defining fields after workflow initialization or require controlled reissue |
| Capsule packing configuration was previously generic `filling` | Legacy activation could fail to activate blister/bulk | Resolver corrected; apply migration and test both capsule routes |
| SQLite is present for development/testing | Not suitable as the production validation database without approval | Use approved production database and perform IQ |
| Source contains pre-existing encoding/mojibake strings in some logs/docs | Console logging may fail on Windows and reduce diagnostic quality | Standardize UTF-8 logging and test operational logs |
| Some features are database/configuration-driven | Incorrect settings can change workflow behavior | Restrict admin access, version settings and test changes |
| Real-time notification delivery depends on server/channel configuration | Users may miss time-critical notifications | Test WebSocket fallback, persistence and acknowledgement |
| Existing validation claims may exceed executed evidence | Inspection and release risk | Mark documents draft until signed tests are complete |

## 11. Recommended standard-review evidence pack

Submit the following together:

1. This capability dossier.
2. Approved URS.
3. Functional and technical risk assessment.
4. Data-flow and system architecture diagram.
5. Role-permission matrix.
6. Approved workflow diagrams for each product route.
7. IQ protocol and executed IQ report.
8. OQ protocol with signed evidence and deviation records.
9. PQ protocol using representative batches and users.
10. Requirements traceability matrix with actual test references.
11. SOPs for operation, access, backup, restore, incident management, change control and periodic review.
12. Training records.
13. Backup/restore and disaster-recovery evidence.
14. Security review and vulnerability results.
15. Final validation summary report and QA release decision.

## 12. Acceptance recommendation

The system is suitable to proceed to controlled validation and standards review. It should not be declared fully validated or released for unrestricted GMP production use until:

- the latest migrations are applied in the approved environment;
- both blister and bulk routes are tested end to end;
- the stale-workflow/product-change control is approved;
- electronic signatures and audit trails are verified;
- IQ, OQ and PQ are executed and approved;
- all critical/high deviations are closed or formally accepted by QA;
- procedures, training and backup evidence are complete.

## 13. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| System Owner |  |  |  |
| IT Manager |  |  |  |
| QA Manager |  |  |  |
| Regulatory Affairs |  |  |  |
| Validation Lead |  |  |  |

