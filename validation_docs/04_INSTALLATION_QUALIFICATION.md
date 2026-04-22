# INSTALLATION QUALIFICATION (IQ)
## Kampala Pharmaceutical Industries - Operations Management System
## Installation Checklist and Verification Protocol

---

**Document Information**

| Item | Details |
|------|---------|
| Document Number | IQ-KPI-OPS-001 |
| Version | 1.0 |
| Date | February 5, 2026 |
| System Name | KPI Operations Management System |
| Prepared By | IT Department |
| Status | Ready for Execution |

---

## TABLE OF CONTENTS

1. [Introduction](#1-introduction)
2. [Installation Environment](#2-installation-environment)
3. [Pre-Installation Checklist](#3-pre-installation-checklist)
4. [Software Installation](#4-software-installation)
5. [Database Setup](#5-database-setup)
6. [System Configuration](#6-system-configuration)
7. [Security Configuration](#7-security-configuration)
8. [Backup and Recovery](#8-backup-and-recovery)
9. [Documentation](#9-documentation)
10. [Acceptance Criteria](#10-acceptance-criteria)

---

## 1. INTRODUCTION

### 1.1 Purpose
This Installation Qualification (IQ) verifies that the KPI Operations Management System hardware and software have been properly installed and configured according to specifications.

### 1.2 Scope
IQ covers:
- Server hardware verification
- Operating system verification
- Software installation (Python, Django, dependencies)
- Database installation and configuration
- Application installation from GitHub
- Security configuration
- Backup procedures
- Documentation

### 1.3 Prerequisites
- Server hardware available
- Network connectivity established
- Administrator access credentials
- GitHub repository access
- This IQ document printed or accessible

---

## 2. INSTALLATION ENVIRONMENT

### 2.1 Hardware Specifications

**Server Details:**

| Item | Specification | Actual | ✓ |
|------|--------------|--------|---|
| Server Type | Physical / VPS / Cloud | __________ | ⃝ |
| Manufacturer/Provider | Dell / HP / AWS / Azure / Other | __________ | ⃝ |
| CPU | Minimum 4 cores | __________ | ⃝ |
| RAM | Minimum 8 GB | __________ | ⃝ |
| Storage | Minimum 100 GB | __________ | ⃝ |
| Storage Type | SSD Preferred | __________ | ⃝ |
| Network | 1 Gbps | __________ | ⃝ |

**Verified By**: _________________ **Date**: _________

---

### 2.2 Operating System

| Item | Specification | Actual | ✓ |
|------|--------------|--------|---|
| OS Type | Windows Server 2019+ OR Ubuntu 20.04+ | __________ | ⃝ |
| OS Version | __________ | __________ | ⃝ |
| OS Architecture | 64-bit | __________ | ⃝ |
| Latest Updates | Security patches applied | __________ | ⃝ |
| Antivirus | Installed and updated | __________ | ⃝ |
| Firewall | Enabled | __________ | ⃝ |

**Verified By**: _________________ **Date**: _________

---

### 2.3 Network Configuration

| Item | Specification | Actual | ✓ |
|------|--------------|--------|---|
| Server Hostname | __________ | __________ | ⃝ |
| IP Address | Static IP (production) | __________ | ⃝ |
| DNS Configuration | Configured | __________ | ⃝ |
| Domain Name (if applicable) | __________ | __________ | ⃝ |
| Firewall Ports Open | 80 (HTTP), 443 (HTTPS) | __________ | ⃝ |
| Internal Network Access | Production floor tablets can reach server | __________ | ⃝ |

**Verified By**: _________________ **Date**: _________

---

## 3. PRE-INSTALLATION CHECKLIST

### 3.1 Documentation Available

| Document | Available | Location | ✓ |
|----------|-----------|----------|---|
| URS Document | ⃝ Yes ⃝ No | __________ | ⃝ |
| OQ Protocol | ⃝ Yes ⃝ No | __________ | ⃝ |
| Installation Guide | ⃝ Yes ⃝ No | __________ | ⃝ |
| README.md | ⃝ Yes ⃝ No | __________ | ⃝ |
| This IQ Document | ⃝ Yes ⃝ No | __________ | ⃝ |

---

### 3.2 Access Credentials

| Item | Available | ✓ |
|------|-----------|---|
| Server administrator username/password | ⃝ Yes | ⃝ |
| Database administrator credentials | ⃝ Yes | ⃝ |
| GitHub repository access | ⃝ Yes | ⃝ |
| SSL certificate (if production) | ⃝ Yes ⃝ N/A | ⃝ |

---

### 3.3 Backup Plan

| Item | Verified | ✓ |
|------|----------|---|
| Backup storage location identified | ⃝ Yes | ⃝ |
| Backup schedule defined | ⃝ Yes | ⃝ |
| Backup restoration tested | ⃝ Pending | ⃝ |

---

## 4. SOFTWARE INSTALLATION

### 4.1 Python Installation

**Step 1: Install Python**

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Install Python 3.11 or higher | Python installed | __________ | ⃝ |
| Verify Python version | `python --version` shows 3.11+ | __________ | ⃝ |
| Verify pip installed | `pip --version` shows version | __________ | ⃝ |

**Commands (Windows):**
```powershell
# Download from python.org or use Chocolatey
choco install python --version=3.11.7
python --version
pip --version
```

**Commands (Linux):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
python3.11 --version
pip3 --version
```

**Verified By**: _________________ **Date**: _________

---

### 4.2 Git Installation

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Install Git | Git installed | __________ | ⃝ |
| Verify Git version | `git --version` shows version | __________ | ⃝ |

**Commands:**
```bash
# Windows
choco install git

# Linux
sudo apt install git
```

**Verified By**: _________________ **Date**: _________

---

### 4.3 PostgreSQL Installation (Production)

**Note**: Skip this section if using SQLite for testing

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Install PostgreSQL 14+ | PostgreSQL installed | __________ | ⃝ |
| Verify PostgreSQL running | Service status = Running | __________ | ⃝ |
| Create database | Database "kpi_production" created | __________ | ⃝ |
| Create database user | User "kpi_user" created | __________ | ⃝ |
| Set user password | Password set and recorded | __________ | ⃝ |
| Grant permissions | User has access to database | __________ | ⃝ |

**Commands:**
```sql
-- After installing PostgreSQL
CREATE DATABASE kpi_production;
CREATE USER kpi_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE kpi_production TO kpi_user;
```

**Database Credentials** (store securely, not in this document):
- Database Name: kpi_production
- Username: kpi_user
- Password: [STORED IN PASSWORD MANAGER]

**Verified By**: _________________ **Date**: _________

---

### 4.4 Redis Installation (Optional - for Production)

**Note**: Required only if using WebSockets/real-time features

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Install Redis | Redis installed | __________ | ⃝ |
| Verify Redis running | Service status = Running | __________ | ⃝ |
| Test Redis connection | `redis-cli ping` returns PONG | __________ | ⃝ |

**Verified By**: _________________ **Date**: _________

---

## 5. DATABASE SETUP

### 5.1 Clone Repository

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Clone from GitHub | Repository downloaded | __________ | ⃝ |
| Verify branch | On correct branch (main or production) | __________ | ⃝ |
| Check files present | manage.py exists in root | __________ | ⃝ |

**Commands:**
```bash
cd /path/to/installation
git clone https://github.com/kyamanywa/portalfor-pharma.git
cd portalfor-pharma
git branch
ls -l manage.py
```

**Installation Path**: ________________________________________

**Verified By**: _________________ **Date**: _________

---

### 5.2 Create Virtual Environment

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Create venv | Virtual environment created | __________ | ⃝ |
| Activate venv | Prompt shows (venv) | __________ | ⃝ |
| Verify Python in venv | `which python` shows venv path | __________ | ⃝ |

**Commands (Windows):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Commands (Linux):**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

**Verified By**: _________________ **Date**: _________

---

### 5.3 Install Python Dependencies

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Install from requirements.txt | All packages installed | __________ | ⃝ |
| Verify Django installed | `python -m django --version` shows 4.2.7 | __________ | ⃝ |
| Verify all packages | `pip list` shows all required packages | __________ | ⃝ |
| Check for errors | No installation errors | __________ | ⃝ |

**Commands:**
```bash
pip install -r requirements.txt
python -m django --version
pip list
```

**Package Count Expected**: 27+ packages

**Verified By**: _________________ **Date**: _________

---

### 5.4 Database Migrations

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Run makemigrations | Migration files created (if any) | __________ | ⃝ |
| Run migrate | Database tables created | __________ | ⃝ |
| Verify tables created | 30+ tables exist | __________ | ⃝ |
| No migration errors | All migrations successful | __________ | ⃝ |

**Commands:**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Verified By**: _________________ **Date**: _________

---

### 5.5 Collect Static Files

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Run collectstatic | Static files copied | __________ | ⃝ |
| Verify static directory | staticfiles/ directory exists | __________ | ⃝ |
| Check file count | 100+ files copied | __________ | ⃝ |

**Commands:**
```bash
python manage.py collectstatic --noinput
```

**Verified By**: _________________ **Date**: _________

---

## 6. SYSTEM CONFIGURATION

### 6.1 Settings Configuration

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Review kampala_pharma/settings.py | File accessible | __________ | ⃝ |
| Set DEBUG = False (production) | DEBUG = False | __________ | ⃝ |
| Generate new SECRET_KEY | Unique secret key set | __________ | ⃝ |
| Configure ALLOWED_HOSTS | Server IP/domain added | __________ | ⃝ |
| Configure DATABASE settings | PostgreSQL connection configured | __________ | ⃝ |
| Set SECURE_SSL_REDIRECT (prod) | HTTPS enforced | __________ | ⃝ |

**ALLOWED_HOSTS Configuration**:
```python
ALLOWED_HOSTS = ['your-server-ip', 'yourdomain.com', 'localhost']
```

**Verified By**: _________________ **Date**: _________

---

### 6.2 Create Superuser Account

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Run createsuperuser | Superuser created | __________ | ⃝ |
| Record username | Username documented | __________ | ⃝ |
| Set strong password | Password meets complexity | __________ | ⃝ |
| Record employee ID | Employee ID documented | __________ | ⃝ |

**Commands:**
```bash
python manage.py createsuperuser
```

**Superuser Credentials** (store securely):
- Username: __________
- Password: [STORED IN PASSWORD MANAGER]
- Employee ID: __________

**Verified By**: _________________ **Date**: _________

---

### 6.3 Create Test Users (For OQ Testing)

| Role | Username | Created | ✓ |
|------|----------|---------|---|
| QA | qa_test | ⃝ | ⃝ |
| Regulatory | reg_test | ⃝ | ⃝ |
| Production Manager | pm_test | ⃝ | ⃝ |
| QC | qc_test | ⃝ | ⃝ |
| Store Manager | store_test | ⃝ | ⃝ |
| Mixing Operator | mix_op_test | ⃝ | ⃝ |
| Granulation Operator | gran_op_test | ⃝ | ⃝ |
| Blending Operator | blend_op_test | ⃝ | ⃝ |
| Compression Operator | comp_op_test | ⃝ | ⃝ |
| Packing Operator | pack_op_test | ⃝ | ⃝ |

**Note**: Create via Django Admin or management command

**Verified By**: _________________ **Date**: _________

---

### 6.4 Create Test Products

| Product | Type | Created | ✓ |
|---------|------|---------|---|
| Paracetamol 500mg Tablets | Tablet (Uncoated, Normal) | ⃝ | ⃝ |
| Ibuprofen 200mg Tablets | Tablet (Coated, Normal) | ⃝ | ⃝ |
| Diclofenac Gel 1% | Ointment | ⃝ | ⃝ |
| Amoxicillin 250mg Capsules | Capsule | ⃝ | ⃝ |

**Verified By**: _________________ **Date**: _________

---

## 7. SECURITY CONFIGURATION

### 7.1 Application Security

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| DEBUG = False in production | Confirmed | __________ | ⃝ |
| SECRET_KEY is unique and secure | Confirmed | __________ | ⃝ |
| CSRF protection enabled | Confirmed (Django default) | __________ | ⃝ |
| Session security configured | SECURE_COOKIE flags set | __________ | ⃝ |
| Password hashing enabled | PBKDF2 algorithm (Django default) | __________ | ⃝ |

**Verified By**: _________________ **Date**: _________

---

### 7.2 Server Security

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Firewall configured | Only necessary ports open | __________ | ⃝ |
| SSH key-based auth (Linux) | Password login disabled | __________ | ⃝ |
| Automatic security updates | Enabled | __________ | ⃝ |
| Fail2ban installed (Linux) | Brute force protection | __________ | ⃝ |
| Antivirus running | Up-to-date signatures | __________ | ⃝ |

**Verified By**: _________________ **Date**: _________

---

### 7.3 SSL Certificate (Production)

**Note**: Required for production, optional for testing

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| SSL certificate obtained | Certificate file available | __________ | ⃝ |
| Certificate installed | HTTPS working | __________ | ⃝ |
| Certificate valid | No browser warnings | __________ | ⃝ |
| Auto-renewal configured | Certbot/renewal script setup | __________ | ⃝ |
| HTTP → HTTPS redirect | Automatic redirect working | __________ | ⃝ |

**Certificate Details**:
- Issuer: __________
- Expiry Date: __________
- Domain: __________

**Verified By**: _________________ **Date**: _________

---

## 8. BACKUP AND RECOVERY

### 8.1 Backup Configuration

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Backup script created | Script exists and tested | __________ | ⃝ |
| Backup schedule configured | Daily backups automated | __________ | ⃝ |
| Backup storage location | Offsite or separate drive | __________ | ⃝ |
| Backup includes database | Database dump script working | __________ | ⃝ |
| Backup includes code | Git repository backed up | __________ | ⃝ |
| Backup includes media files | Media directory backed up | __________ | ⃝ |

**Backup Schedule**: Daily at __________ (time)

**Backup Retention**: __________ days

**Verified By**: _________________ **Date**: _________

---

### 8.2 Restore Test

| Task | Expected Result | Actual Result | ✓ |
|------|----------------|---------------|---|
| Create test backup | Backup file created | __________ | ⃝ |
| Simulate data loss | Test data deleted | __________ | ⃝ |
| Restore from backup | Data restored successfully | __________ | ⃝ |
| Verify data integrity | All data intact and accessible | __________ | ⃝ |
| Document restore procedure | Restore SOP created | __________ | ⃝ |

**Restore Time**: __________ (time to complete restore)

**Verified By**: _________________ **Date**: _________

---

## 9. DOCUMENTATION

### 9.1 Installation Documentation

| Document | Status | Location | ✓ |
|----------|--------|----------|---|
| Server specifications | ⃝ Complete | __________ | ⃝ |
| Network diagram | ⃝ Complete | __________ | ⃝ |
| Software versions log | ⃝ Complete | __________ | ⃝ |
| Configuration file backup | ⃝ Complete | __________ | ⃝ |
| Admin credentials (secure) | ⃝ Complete | __________ | ⃝ |
| This completed IQ document | ⃝ Complete | __________ | ⃝ |

---

### 9.2 SOPs Created

| SOP | Status | ✓ |
|-----|--------|---|
| System Startup/Shutdown | ⃝ Created | ⃝ |
| Backup and Restore | ⃝ Created | ⃝ |
| User Account Management | ⃝ Created | ⃝ |
| System Monitoring | ⃝ Created | ⃝ |
| Incident Response | ⃝ Created | ⃝ |

---

## 10. ACCEPTANCE CRITERIA

### 10.1 Installation Acceptance

IQ is considered complete and acceptable when:

**Hardware/Infrastructure**
- ✓ Server meets minimum specifications
- ✓ Network connectivity verified
- ✓ Operating system installed and updated
- ✓ Security measures implemented

**Software Installation**
- ✓ Python 3.11+ installed
- ✓ All Python dependencies installed (27+ packages)
- ✓ Database software installed (PostgreSQL or SQLite)
- ✓ Application code cloned from GitHub

**Database Configuration**
- ✓ Database created and configured
- ✓ All migrations applied successfully
- ✓ 30+ tables created
- ✓ Static files collected

**System Configuration**
- ✓ Settings.py configured correctly
- ✓ Superuser account created
- ✓ Test users created
- ✓ Test products created

**Security**
- ✓ DEBUG = False (production)
- ✓ Unique SECRET_KEY generated
- ✓ ALLOWED_HOSTS configured
- ✓ Firewall configured
- ✓ SSL certificate installed (production)

**Backup/Recovery**
- ✓ Backup procedures implemented
- ✓ Restore procedure tested and documented
- ✓ Backup schedule automated

**Documentation**
- ✓ All installation steps documented
- ✓ Configuration documented
- ✓ Credentials stored securely
- ✓ SOPs created

**Functionality**
- ✓ System accessible via web browser
- ✓ Login page displays
- ✓ Admin login works
- ✓ Database connectivity verified
- ✓ No critical errors in logs

---

### 10.2 IQ Test Summary

**Total Verification Items**: Count all checkboxes above

**Items Verified**: __________ / __________

**Pass Rate**: __________%

**Acceptance Criteria**: 100% of critical items verified, ≥95% overall

**Status**: ⃝ PASS  ⃝ FAIL  ⃝ PASS WITH DEVIATIONS

---

### 10.3 Deviations

**If any items failed, document here:**

| Item # | Description | Impact | Resolution | Status |
|--------|-------------|--------|------------|--------|
| | | | | |
| | | | | |
| | | | | |

---

## APPROVAL SIGNATURES

**Installation Performed By:**

| Name | Role | Signature | Date |
|------|------|-----------|------|
| _________________ | IT Administrator | _________________ | __________ |
| _________________ | System Administrator | _________________ | __________ |

**Installation Reviewed By:**

| Name | Role | Signature | Date |
|------|------|-----------|------|
| _________________ | IT Manager | _________________ | __________ |
| _________________ | QA Manager | _________________ | __________ |

**Installation Approved By:**

| Name | Role | Signature | Date |
|------|------|-----------|------|
| _________________ | QA Manager | _________________ | __________ |
| _________________ | IT Manager | _________________ | __________ |

---

## POST-INSTALLATION CHECKLIST

**Before proceeding to OQ:**

- [ ] IQ document 100% complete
- [ ] All critical items verified
- [ ] Deviations (if any) documented and resolved
- [ ] All approvals obtained
- [ ] System accessible and stable
- [ ] Backup verified functional
- [ ] Ready to begin Operational Qualification (OQ)

**Next Step**: Proceed to `02_OPERATIONAL_QUALIFICATION.md` for functional testing

---

**Document Control**
- Installation Date: __________
- IQ Completion Date: __________
- Document Location: Validation Files / QMS

---

**END OF INSTALLATION QUALIFICATION**
