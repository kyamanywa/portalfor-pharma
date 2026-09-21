from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from dashboards.bmr_form_views import (
    QA_GENERIC_MODE_PHASES,
    QA_PHASE_SPECIFIC_MODES,
    can_access_sorting_ipc_form,
)
from dashboards.models import (
    QMSAction, QMSCAPA, QMSCalibrationEvent, QMSCalibrationRecord, QMSChangeControl,
    QMSDocument, QMSQualityQuery, QMSRecordLink, QMSRegulatoryPackage,
    QMSLabInvestigation, QMSStabilitySchedule, QMSStabilityResult, QMSCOA,
    QMSMaterialQC, QMSSupplierQualification,
)


class SortingIPCTest(SimpleTestCase):
    def test_qa_can_access_ipc_when_section_a_is_signed_and_personnel_exists(self):
        phase_data = {
            'sorting_sections': {
                'section_statuses': {
                    'inspection_recon': 'qa_signed',
                    'personnel': 'completed',
                },
                'personnel': {'person_a': 'Alice'},
            }
        }
        self.assertTrue(can_access_sorting_ipc_form(phase_data, 'qa'))

    def test_qa_cannot_access_ipc_without_section_a_signature(self):
        phase_data = {
            'sorting_sections': {
                'section_statuses': {
                    'inspection_recon': 'operator_filled',
                    'personnel': 'completed',
                },
                'personnel': {'person_a': 'Alice'},
            }
        }
        self.assertFalse(can_access_sorting_ipc_form(phase_data, 'qa'))


class SortingTemplateScrollTest(SimpleTestCase):
    def test_bmr_template_prioritizes_hash_anchor_for_qa_scroll(self):
        template_path = Path(__file__).resolve().parent.parent / 'templates' / 'bmr' / 'bmr_detail_new.html'
        content = template_path.read_text(encoding='utf-8')

        self.assertIn("var hash = (window.location.hash || '').replace('#','').trim();", content)
        self.assertIn("var target = document.getElementById(hash);", content)


class CompressionQAModeTest(SimpleTestCase):
    def test_compression_qa_uses_qa_signing_mode(self):
        self.assertNotIn('compression', QA_PHASE_SPECIFIC_MODES)
        self.assertIn('compression', QA_GENERIC_MODE_PHASES)

    def test_compression_template_keeps_qa_signature_controls(self):
        template_path = Path(__file__).resolve().parent.parent / 'templates' / 'bmr' / 'bmr_detail_new.html'
        content = template_path.read_text(encoding='utf-8')

        self.assertIn('name="action" value="qa_sign_section_compression_timing_yield"', content)
        self.assertIn('name="action" value="qa_sign_section_compression_dies_punches"', content)
        self.assertIn("compression_section_statuses.timing_yield == 'operator_filled' and edit_mode == 'qa'", content)
        self.assertIn("compression_section_statuses.dies_punches == 'operator_filled' and edit_mode == 'qa'", content)


class PageHeaderDatePersistenceTest(SimpleTestCase):
    def test_page_headers_are_synced_into_section_submissions(self):
        template_path = Path(__file__).resolve().parent.parent / 'templates' / 'bmr' / 'bmr_detail_new.html'
        content = template_path.read_text(encoding='utf-8')

        self.assertIn("document.querySelectorAll('.bmr-shift-select, .bmr-date-input')", content)
        self.assertIn("data-page-header-sync=\"true\"", content)
        self.assertIn("hidden.name = field.name", content)
        self.assertIn('window.syncBmrPageHeaders(form);', content)


class MaterialDispensingTemplateTest(SimpleTestCase):
    def test_bmr_template_renders_dynamic_dispensing_pages(self):
        template_path = Path(__file__).resolve().parent.parent / 'templates' / 'bmr' / 'bmr_detail_new.html'
        content = template_path.read_text(encoding='utf-8')

        self.assertIn("{% for ingredient_page in ingredient_pages %}", content)
        self.assertIn("is_last_page=forloop.last", content)

    def test_tablet_store_template_keeps_submission_controls(self):
        template_path = Path(__file__).resolve().parent.parent / 'templates' / 'bmr' / 'bmr_detail_new.html'
        content = template_path.read_text(encoding='utf-8')

        for marker in (
            "{% if edit_mode == 'store' %}",
            'name="action" value="save_draft"',
            'name="action" value="complete"',
            'id="completeStoreBtn"',
            'Complete &amp; Submit to Dispensing',
            'name="action" value="recall_store"',
        ):
            self.assertIn(marker, content)

    def test_capsule_store_template_keeps_submission_controls(self):
        template_path = Path(__file__).resolve().parent.parent / 'templates' / 'bmr' / 'bmr_capsule.html'
        content = template_path.read_text(encoding='utf-8')

        for marker in (
            "{% if edit_mode == 'store' %}",
            'name="action" value="save_draft"',
            'name="action" value="complete"',
            'id="completeStoreBtn"',
            'Complete &amp; Submit to Dispensing',
            'name="action" value="recall_store"',
        ):
            self.assertIn(marker, content)


class QADashboardPendingCountTest(TestCase):
    def test_hidden_qms_workspace_items_do_not_inflate_qa_operations_pending_count(self):
        user = get_user_model().objects.create_user(
            username='qa-dashboard-user',
            password='test-pass',
            role='qa',
        )
        QMSAction.objects.create(
            category='deviation',
            owner_role='qa',
            title='Hidden Head QA QMS item',
            description='This QMS item belongs in the QMS/Head QA workspace.',
            created_by=user,
            assigned_to=user,
        )

        client = Client()
        client.force_login(user)
        response = client.get(reverse('dashboards:qa_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['show_qms_workspace'])
        self.assertEqual(response.context['qa_qms_stats']['total'], 1)
        self.assertEqual(response.context['grand_total_pending'], 0)


class CAPALifecycleModelTest(TestCase):
    def test_capa_requires_effectiveness_and_approval_before_closure(self):
        user = get_user_model().objects.create_user(username='capa-owner', password='test-pass')
        action = QMSAction.objects.create(
            category='capa',
            owner_role='qa',
            title='Investigate recurring compression deviation',
            description='Recurring tablet hardness deviation.',
            created_by=user,
            assigned_to=user,
        )
        capa = QMSCAPA.objects.create(
            qms_action=action,
            created_by=user,
            action_owner=user,
            problem_statement='Recurring deviation identified.',
            root_cause_analysis='Insufficient calibration control.',
            corrective_action_plan='Recalibrate equipment.',
            preventive_action_plan='Add quarterly verification.',
            effectiveness_result='effective',
            effectiveness_evidence='Three consecutive compliant lots.',
            effectiveness_verified_by=user,
            effectiveness_review_date='2026-08-03',
            approved_by=user,
        )
        self.assertTrue(capa.is_ready_for_closure)
        self.assertTrue(capa.capa_number.startswith('CAPA'))

    def test_new_capa_detail_template_contains_controlled_workflow_sections(self):
        template_path = Path(__file__).resolve().parent.parent / 'templates' / 'dashboards' / 'qms' / 'capa_detail.html'
        content = template_path.read_text(encoding='utf-8')
        for section in ('Root cause analysis', 'Corrective action plan', 'Preventive action plan', 'Effectiveness result', 'Submit for QA review', 'Close CAPA'):
            self.assertIn(section, content)


class ChangeControlLifecycleModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='change-owner', password='test-pass')
        self.action = QMSAction.objects.create(
            category='change_control', owner_role='qa', title='Update tablet press calibration schedule',
            description='Controlled change to the calibration programme.', created_by=self.user,
            assigned_to=self.user, priority='high', status='action_required',
        )
        self.change = QMSChangeControl.objects.create(
            qms_action=self.action, created_by=self.user, owner=self.user,
            change_type='equipment', risk_level='high', justification='Prevent recurrence of deviation.',
            current_state='Ad hoc calibration.', proposed_state='Quarterly documented calibration.',
            impact_summary='Quality and GMP impact assessed.', quality_impact=True, gmp_impact=True,
            implementation_plan='Issue schedule and complete calibration.', implementation_owner=self.user,
            implementation_notes='Calibration schedule issued and equipment recalibrated.',
            planned_implementation_date='2026-08-15', actual_implementation_date='2026-08-01',
            effectiveness_method='Review three compliant lots.', effectiveness_criteria='Three lots meet specification.',
            effectiveness_result='effective', effectiveness_evidence='Three compliant lots verified.',
            effectiveness_verified_by=self.user, effectiveness_review_date='2026-08-03', approved_by=self.user,
        )

    def test_change_control_requires_impact_and_effectiveness_gates(self):
        self.assertTrue(self.change.ready_for_approval)
        self.assertTrue(self.change.ready_for_closure)
        self.assertTrue(self.change.change_number.startswith('CC'))

    def test_change_control_template_contains_full_lifecycle_sections(self):
        template_path = Path(__file__).resolve().parent.parent / 'templates' / 'dashboards' / 'qms' / 'change_control_detail.html'
        content = template_path.read_text(encoding='utf-8')
        for section in ('Impact Assessment', 'Implementation', 'Effectiveness', 'Submit for QA review', 'Close Change'):
            self.assertIn(section, content)


class QMSRecordLinkTest(TestCase):
    def test_cross_module_relationship_is_unique_and_auditable(self):
        user = get_user_model().objects.create_user(username='link-user', password='test-pass')
        source = QMSAction.objects.create(
            category='change_control', owner_role='qa', title='Controlled equipment change',
            description='Link source action.', created_by=user, assigned_to=user,
        )
        capa_action = QMSAction.objects.create(
            category='capa', owner_role='qa', title='Related CAPA action',
            description='Link target action.', created_by=user, assigned_to=user,
        )
        capa = QMSCAPA.objects.create(qms_action=capa_action, created_by=user, action_owner=user)
        link, created = QMSRecordLink.objects.get_or_create(
            from_content_type=ContentType.objects.get_for_model(source), from_object_id=source.pk,
            to_content_type=ContentType.objects.get_for_model(capa), to_object_id=capa.pk,
            link_type='addresses', defaults={'rationale': 'Change implements CAPA action.', 'created_by': user},
        )
        duplicate, duplicate_created = QMSRecordLink.objects.get_or_create(
            from_content_type=ContentType.objects.get_for_model(source), from_object_id=source.pk,
            to_content_type=ContentType.objects.get_for_model(capa), to_object_id=capa.pk,
            link_type='addresses', defaults={'created_by': user},
        )
        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(link.pk, duplicate.pk)
        self.assertEqual(QMSRecordLink.objects.count(), 1)


class DocumentsAndQueriesLifecycleTest(TestCase):
    def test_document_and_query_have_controlled_readiness_gates(self):
        user = get_user_model().objects.create_user(username='documents-query-user', password='test-pass')
        document = QMSDocument.objects.create(
            document_type='sop', title='Calibration SOP', version='2.0', owner=user,
            controlled_file=SimpleUploadedFile('calibration.pdf', b'controlled content', content_type='application/pdf'),
            reviewed_by=user, review_comments='Reviewed against current calibration practice.',
            approved_by=user, effective_date='2026-08-04',
        )
        query = QMSQualityQuery.objects.create(
            query_type='regulatory', subject='Regulatory clarification', question='Clarify submission requirement.',
            assigned_to=user, investigation_notes='Requirement reviewed with QA.', response='Response prepared.',
            responded_by=user, qa_approved_by=user, resolution='Response issued and archived.',
        )
        self.assertTrue(document.ready_for_review)
        self.assertTrue(document.ready_for_approval)
        self.assertTrue(document.ready_for_effective)
        self.assertTrue(query.ready_for_qa_review)
        self.assertTrue(query.ready_for_close)

    def test_document_and_query_workspaces_exist(self):
        document_template = Path(__file__).resolve().parent.parent / 'templates' / 'dashboards' / 'qms' / 'document_detail.html'
        query_template = Path(__file__).resolve().parent.parent / 'templates' / 'dashboards' / 'qms' / 'quality_query_detail.html'
        self.assertIn('Controlled Document Management', document_template.read_text(encoding='utf-8'))
        self.assertIn('Quality Query & Correspondence', query_template.read_text(encoding='utf-8'))


class RegulatoryPackageWorkflowTest(TestCase):
    def test_package_runs_from_intake_to_authority_approval_and_closure(self):
        user = get_user_model().objects.create_user(username='regulatory-workflow-user', password='test-pass', is_staff=True)
        document = QMSDocument.objects.create(
            document_type='sop', title='Regulatory Submission SOP', version='1.0', owner=user,
            controlled_file=SimpleUploadedFile('submission-sop.pdf', b'controlled content', content_type='application/pdf'),
            status='effective', reviewed_by=user, review_comments='QA reviewed.', approved_by=user,
            effective_date='2026-08-04',
        )
        package = QMSRegulatoryPackage.objects.create(
            title='Regulatory workflow test package', owner=user, market='UG', authority='NDA', status='draft',
        )
        package.included_documents.add(document)
        client = Client()
        client.force_login(user)
        url = reverse('dashboards:qms_regulatory_package_detail', kwargs={'package_id': package.id})
        common = {
            'title': package.title, 'market': 'UG', 'authority': 'NDA', 'owner': str(user.id),
            'scope_summary': 'Tablet product registration scope.', 'dossier_summary': 'Administrative, quality, and clinical sections compiled.',
            'included_documents': str(document.id), 'qa_reviewer': str(user.id),
        }

        response = client.post(url, {**common, 'package_operation': 'submit_qa'})
        self.assertEqual(response.status_code, 302)
        package.refresh_from_db()
        self.assertEqual(package.status, 'qa_review')

        response = client.post(url, {**common, 'package_operation': 'approve_internal', 'internal_approval_date': '2026-08-04', 'internal_qa_notes': 'QA review complete; dossier is ready for submission.'})
        self.assertEqual(response.status_code, 302)
        package.refresh_from_db()
        self.assertEqual(package.status, 'submitted')
        self.assertEqual(package.submitted_by_id, user.id)

        response = client.post(url, {**common, 'package_operation': 'authority_approve', 'authority_reference': 'NDA-TEST-001', 'authority_response': 'Marketing authorization approved.', 'authority_response_date': '2026-08-04', 'outcome_notes': 'Approval recorded and commitments tracked.'})
        self.assertEqual(response.status_code, 302)
        package.refresh_from_db()
        self.assertEqual(package.status, 'approved')
        self.assertEqual(package.approved_by_id, user.id)

        response = client.post(url, {**common, 'package_operation': 'close', 'outcome_notes': 'Package closed after authority approval and commitment handoff.'})
        self.assertEqual(response.status_code, 302)
        package.refresh_from_db()
        self.assertEqual(package.status, 'closed')


class ControlledDocumentApprovalGateTest(TestCase):
    def test_document_without_file_cannot_be_approved_or_marked_approved_directly(self):
        user = get_user_model().objects.create_user(username='document-qa-user', password='test-pass', is_staff=True)
        document = QMSDocument.objects.create(
            document_type='sop', title='Missing controlled file SOP', version='1.0', owner=user,
            status='in_review', reviewed_by=user, review_comments='Reviewed content.',
        )
        client = Client()
        client.force_login(user)
        url = reverse('dashboards:qms_document_detail', kwargs={'document_id': document.id})

        response = client.post(url, {'document_operation': 'approve'})
        self.assertEqual(response.status_code, 302)
        document.refresh_from_db()
        self.assertEqual(document.status, 'in_review')

        response = client.post(url, {'status': 'approved'})
        self.assertEqual(response.status_code, 302)
        document.refresh_from_db()
        self.assertEqual(document.status, 'in_review')


class CalibrationWorkflowTest(TestCase):
    def test_calibration_event_certificate_and_qa_verification_are_auditable(self):
        user = get_user_model().objects.create_user(username='calibration-qa-user', password='test-pass', is_staff=True)
        calibration = QMSCalibrationRecord.objects.create(
            equipment_id='EQ-001', equipment_name='Tablet Press', department='Production', owner=user, created_by=user,
            calibration_interval_days=365, method_reference='CAL-SOP-001', acceptance_criteria='Within approved tolerance.',
        )
        client = Client()
        client.force_login(user)
        url = reverse('dashboards:qms_calibration_detail', kwargs={'calibration_id': calibration.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        response = client.post(url, {
            'calibration_operation': 'record_calibration', 'equipment_id': calibration.equipment_id,
            'equipment_name': calibration.equipment_name, 'owner': str(user.id), 'calibration_date': '2026-08-04',
            'result': 'pass', 'certificate_number': 'CERT-001', 'event_notes': 'Calibration completed within tolerance.',
            'event_certificate_file': SimpleUploadedFile('cert-001.pdf', b'certificate', content_type='application/pdf'),
        })
        self.assertEqual(response.status_code, 302)
        calibration.refresh_from_db()
        self.assertEqual(calibration.status, 'in_service')
        self.assertEqual(calibration.events.count(), 1)
        self.assertTrue(calibration.events.first().certificate_file)
        response = client.post(url, {'calibration_operation': 'verify'})
        self.assertEqual(response.status_code, 302)
        calibration.refresh_from_db()
        self.assertEqual(calibration.verified_by_id, user.id)
        self.assertTrue(QMSCalibrationEvent.objects.filter(calibration=calibration, verified_by=user).exists())


class QCEnterpriseWorkflowTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='qc-qa-user', password='test-pass', is_staff=True,
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_oos_investigation_requires_phase_reviews_and_qa_disposition(self):
        investigation = QMSLabInvestigation.objects.create(event_type='oos', test_name='Assay')
        url = reverse('dashboards:qms_lab_investigation_detail', kwargs={'investigation_id': investigation.id})
        response = self.client.post(url, {
            'qc_operation': 'phase2', 'analyst_review': 'Reviewed', 'instrument_review': 'Passed',
            'method_review': 'Current', 'sample_review': 'Intact',
        })
        self.assertEqual(response.status_code, 302)
        investigation.refresh_from_db()
        self.assertEqual(investigation.status, 'phase2_full_investigation')
        self.client.post(url, {'qc_operation': 'submit_qa', 'root_cause': 'Sampling error', 'qa_conclusion': 'Valid investigation', 'disposition': 'valid_result'})
        investigation.refresh_from_db()
        self.assertEqual(investigation.status, 'qa_review')
        self.client.post(url, {'qc_operation': 'approve', 'disposition': 'valid_result'})
        investigation.refresh_from_db()
        self.assertEqual(investigation.status, 'closed')
        self.assertEqual(investigation.qa_reviewer_id, self.user.id)

    def test_stability_result_and_qa_review_lifecycle(self):
        schedule = QMSStabilitySchedule.objects.create(condition='long_term', time_point='T0', pull_date='2026-08-04')
        url = reverse('dashboards:qms_stability_detail', kwargs={'stability_id': schedule.id})
        self.client.post(url, {
            'qc_operation': 'record_result', 'result_test_name': 'Assay', 'result_value': '99.8%',
            'result_specification': '95-105%', 'result_passed': 'true', 'result_test_date': '2026-08-04',
            'result_comments': 'Within specification.', 'result_summary': 'All results passed.',
        })
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, 'tested')
        self.assertEqual(schedule.results.count(), 1)
        self.client.post(url, {'qc_operation': 'submit_qa', 'result_summary': 'All results passed.'})
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, 'qa_review')
        self.client.post(url, {'qc_operation': 'approve', 'qa_review_notes': 'Reviewed and accepted.'})
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, 'reviewed')
        self.assertEqual(schedule.reviewed_by_id, self.user.id)

    def test_coa_cannot_release_without_controlled_file(self):
        coa = QMSCOA.objects.create()
        url = reverse('dashboards:qms_coa_detail', kwargs={'coa_id': coa.id})
        self.client.post(url, {'qc_operation': 'prepare', 'result_summary': 'All final lot tests passed.'})
        self.client.post(url, {'qc_operation': 'submit_qa', 'result_summary': 'All final lot tests passed.'})
        coa.refresh_from_db()
        self.assertEqual(coa.status, 'qa_review')
        self.client.post(url, {'qc_operation': 'approve'})
        coa.refresh_from_db()
        self.assertEqual(coa.status, 'qa_review')
        self.client.post(url, {'qc_operation': 'approve', 'certificate_file': SimpleUploadedFile('coa.pdf', b'approved coa', content_type='application/pdf')})
        coa.refresh_from_db()
        self.assertEqual(coa.status, 'approved')

    def test_qc_register_creates_material_workspace(self):
        response = self.client.post(reverse('dashboards:qms_qc_register'), {
            'qc_record_type': 'material_qc', 'title': 'Lactose monohydrate',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(QMSMaterialQC.objects.filter(material_name='Lactose monohydrate', owner=self.user).exists())
