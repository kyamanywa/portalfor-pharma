"""
QMS Functionality Test - Run via Django shell
Execute: python manage.py shell < run_qms_tests.py
"""

from django.contrib.auth import get_user_model
from dashboards.models import (
    QMSSamplingPlan, QMSLabSpecification, QMSStabilitySchedule,
    QMSSupplierQualification, QMSCalibrationRecord, QMSTrainingRecord,
    QMSRegulatoryPackage, QMSNotificationRule,
    QMSAction, QMSAudit, QMSRiskAssessment, QMSDocument
)
from products.models import Product
from datetime import date, timedelta

User = get_user_model()

print("=" * 70)
print("QMS FUNCTIONALITY TEST SUITE")
print("=" * 70)

# Get test user
test_user = User.objects.filter(is_staff=True).first()
if not test_user:
    test_user = User.objects.first()

test_product = Product.objects.first()

passed = 0
failed = 0

def test(name, func):
    global passed, failed
    try:
        func()
        print(f"✓ {name}")
        passed += 1
        return True
    except Exception as e:
        print(f"✗ {name}: {str(e)}")
        failed += 1
        return False

print("\n[ENTERPRISE QMS MODULES]")

# Test 1: Sampling Plan
def test_sampling():
    plan = QMSSamplingPlan.objects.create(
        product=test_product,
        sample_type='raw_material',
        lot_size_min=100,
        lot_size_max=500,
        aql_level=1.5,
        sample_size=13,
        acceptance=0,
        rejection=1,
        created_by=test_user
    )
    assert plan.sample_size == 13
    plan.sample_size = 20
    plan.save()
    plan.refresh_from_db()
    assert plan.sample_size == 20
    plan.delete()

test("Sampling Plan CRUD", test_sampling)

# Test 2: Lab Specification
def test_lab_spec():
    spec = QMSLabSpecification.objects.create(
        product=test_product,
        test_type='identity',
        parameter='Assay',
        method='HPLC',
        specification='98.0% - 102.0%',
        created_by=test_user
    )
    assert spec.parameter == 'Assay'
    spec.delete()

test("Lab Specification CRUD", test_lab_spec)

# Test 3: Stability Schedule
def test_stability():
    schedule = QMSStabilitySchedule.objects.create(
        product=test_product,
        condition='long_term',
        temperature='25°C ± 2°C',
        humidity='60% RH ± 5%',
        pull_month=6,
        next_pull_date=date.today() + timedelta(days=180),
        created_by=test_user
    )
    assert schedule.pull_month == 6
    schedule.delete()

test("Stability Schedule CRUD", test_stability)

# Test 4: Supplier Qualification
def test_supplier():
    supplier = QMSSupplierQualification.objects.create(
        supplier_name='Test Supplier Ltd',
        material_type='API',
        qualification_status='approved',
        score=85,
        created_by=test_user
    )
    assert supplier.score == 85
    supplier.delete()

test("Supplier Qualification CRUD", test_supplier)

# Test 5: Calibration Record
def test_calibration():
    cal = QMSCalibrationRecord.objects.create(
        equipment_id='HPLC-001',
        equipment_name='HPLC System',
        calibration_type='periodic',
        last_calibration_date=date.today(),
        next_calibration_date=date.today() + timedelta(days=365),
        status='valid',
        created_by=test_user
    )
    assert cal.equipment_id == 'HPLC-001'
    cal.delete()

test("Calibration Record CRUD", test_calibration)

# Test 6: Training Record
def test_training():
    training = QMSTrainingRecord.objects.create(
        trainee=test_user,
        sop_number='SOP-QC-001',
        sop_title='HPLC Operation',
        training_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        status='valid',
        created_by=test_user
    )
    assert training.sop_number == 'SOP-QC-001'
    training.delete()

test("Training Record CRUD", test_training)

# Test 7: Regulatory Package
def test_regulatory():
    package = QMSRegulatoryPackage.objects.create(
        product=test_product,
        package_type='variation',
        submission_type='undc',
        status='preparation',
        created_by=test_user
    )
    assert package.package_type == 'variation'
    package.delete()

test("Regulatory Package CRUD", test_regulatory)

# Test 8: Notification Rule
def test_notification():
    rule = QMSNotificationRule.objects.create(
        event_type='deviation_opened',
        severity='high',
        escalation_hours=24,
        notify_roles='head_qa,qa_manager',
        created_by=test_user
    )
    assert rule.escalation_hours == 24
    rule.delete()

test("Notification Rule CRUD", test_notification)

print("\n[QMS CORE MODULES]")

# Test 9: QMS Action (Change Control/CAPA)
def test_qms_action():
    action = QMSAction.objects.create(
        category='change_control',
        owner_role='qa',
        title='Test Process Change',
        description='Testing change control workflow',
        priority='medium',
        created_by=test_user,
        assigned_to=test_user,
        status='open'
    )
    assert action.qms_number.startswith('QMS')
    action.status = 'closed'
    action.save()
    action.refresh_from_db()
    assert action.status == 'closed'
    action.delete()

test("QMS Action (Change/CAPA) CRUD", test_qms_action)

# Test 10: Audit
def test_audit():
    audit = QMSAudit.objects.create(
        audit_type='internal',
        title='GMP Audit - Production',
        finding_type='minor_nc',
        severity='medium',
        observation='Documentation incomplete',
        status='finding_open',
        created_by=test_user
    )
    assert audit.audit_number.startswith('AUD')
    audit.delete()

test("Audit Management CRUD", test_audit)

# Test 11: Risk Assessment
def test_risk():
    risk = QMSRiskAssessment.objects.create(
        method='fmea',
        title='Granulation Process Risk',
        process_area='Granulation',
        hazard='Temperature deviation',
        severity=7,
        occurrence=3,
        detectability=4,
        owner=test_user,
        status='draft'
    )
    assert risk.risk_number.startswith('RISK')
    assert risk.rpn == 84
    risk.delete()

test("Risk Assessment CRUD", test_risk)

# Test 12: Document
def test_document():
    doc = QMSDocument.objects.create(
        document_type='sop',
        title='Test SOP - HPLC',
        version='1.0',
        status='draft',
        effective_date=None,
        created_by=test_user
    )
    assert doc.document_number.startswith('DOC')
    doc.delete()

test("Document Management CRUD", test_document)

# Summary
print("\n" + "=" * 70)
print("TEST RESULTS")
print("=" * 70)
total = passed + failed
print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
if failed == 0:
    print("✓ ALL TESTS PASSED - QMS FUNCTIONALITY IS WORKING!")
else:
    print(f"⚠ {failed} TEST(S) FAILED")
print("=" * 70)
