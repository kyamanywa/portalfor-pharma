"""
QMS Detail Views - View full record with attachments, comments, and activity history
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db import transaction
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
import mimetypes
from datetime import timedelta
from accounts.signature_security import verify_signature_reauthentication

from .models import (
    QMSAction, QMSCAPA, QMSApprovalRoute, QMSApprovalStep, QMSElectronicSignature,
    QMSAudit, QMSChangeControl, QMSRiskAssessment, QMSDocument, QMSDeviation, QMSAttachment,
    QMSComment, QMSActivityLog, QMSFieldAuditTrail, QMSRecordLink, QMSQualityQuery, QMSRegulatoryPackage, QMSTrainingRecord, QMSCalibrationRecord, QMSCalibrationEvent, QMSLabInvestigation, QMSStabilitySchedule, QMSStabilityResult, QMSCOA, QMSMaterialQC, QMSSupplierQualification
)


QMS_LINKABLE_MODELS = {
    'action': (QMSAction, 'qms_action_detail', 'action_id'),
    'capa': (QMSCAPA, 'qms_capa_detail', 'capa_id'),
    'change_control': (QMSChangeControl, 'qms_change_control_detail', 'change_id'),
    'audit': (QMSAudit, 'qms_audit_detail', 'audit_id'),
    'risk': (QMSRiskAssessment, 'qms_risk_detail', 'risk_id'),
    'document': (QMSDocument, 'qms_document_detail', 'document_id'),
    'deviation': (QMSDeviation, 'qms_deviation_detail', 'deviation_id'),
    'query': (QMSQualityQuery, 'qms_quality_query_detail', 'query_id'),
    'regulatory': (QMSRegulatoryPackage, 'qms_regulatory_package_detail', 'package_id'),
    'training': (QMSTrainingRecord, 'qms_training_detail', 'training_id'),
    'calibration': (QMSCalibrationRecord, 'qms_calibration_detail', 'calibration_id'),
    'oos': (QMSLabInvestigation, 'qms_lab_investigation_detail', 'investigation_id'),
    'stability': (QMSStabilitySchedule, 'qms_stability_detail', 'stability_id'),
    'coa': (QMSCOA, 'qms_coa_detail', 'coa_id'),
    'material_qc': (QMSMaterialQC, 'qms_material_qc_detail', 'material_qc_id'),
    'supplier_quality': (QMSSupplierQualification, 'qms_supplier_quality_detail', 'supplier_id'),
}


def _qms_record_label(record):
    number = next((getattr(record, field, '') for field in (
        'capa_number', 'change_number', 'audit_number', 'risk_number',
        'document_number', 'deviation_number', 'qms_number',
        'query_number',
        'package_number',
        'training_number',
        'equipment_id',
        'investigation_number', 'study_number', 'coa_number', 'material_lot_number', 'supplier_code',
    ) if getattr(record, field, '')), '')
    title = getattr(record, 'title', '') or getattr(record, 'name', '') or getattr(record, 'equipment_name', '')
    return f'{number} · {title}'.strip(' ·')


def _qms_relationship_context(record, source_key):
    content_type = ContentType.objects.get_for_model(record, for_concrete_model=False)
    links = QMSRecordLink.objects.filter(
        Q(from_content_type=content_type, from_object_id=record.pk) |
        Q(to_content_type=content_type, to_object_id=record.pk)
    ).select_related('from_content_type', 'to_content_type', 'created_by')
    linkable_records = []
    for key, (model, url_name, id_kwarg) in QMS_LINKABLE_MODELS.items():
        queryset = model.objects.all().order_by('-pk')[:100]
        for item in queryset:
            if model is record.__class__ and item.pk == record.pk:
                continue
            linkable_records.append({'key': key, 'label': _qms_record_label(item), 'id': item.pk})
    link_rows = []
    for link in links:
        is_from = link.from_content_type_id == content_type.id and link.from_object_id == record.pk
        other_type = link.to_content_type if is_from else link.from_content_type
        other_id = link.to_object_id if is_from else link.from_object_id
        other_key = next((key for key, (model, _, _) in QMS_LINKABLE_MODELS.items() if ContentType.objects.get_for_model(model, for_concrete_model=False).id == other_type.id), None)
        other_spec = QMS_LINKABLE_MODELS.get(other_key)
        other_record = other_spec[0].objects.filter(pk=other_id).first() if other_spec else None
        link_rows.append({
            'link': link,
            'label': _qms_record_label(other_record) if other_record else f'{other_type.model} #{other_id}',
            'direction': link.get_link_type_display() if is_from else f'Linked from: {link.get_link_type_display()}',
            'url': reverse(f'dashboards:{other_spec[1]}', kwargs={other_spec[2]: other_id}) if other_spec and other_record else '',
        })
    return {'qms_links': links, 'qms_link_rows': link_rows, 'qms_link_source_key': source_key, 'qms_linkable_records': linkable_records, 'qms_link_type_choices': QMSRecordLink.LINK_TYPE_CHOICES}


@login_required
@require_POST
def qms_record_link_create(request):
    """Create an auditable relationship between two QMS records."""
    source_key = request.POST.get('source_model')
    target_key = request.POST.get('target_model')
    source_id = request.POST.get('source_id')
    target_id = request.POST.get('target_id')
    source_spec = QMS_LINKABLE_MODELS.get(source_key)
    target_spec = QMS_LINKABLE_MODELS.get(target_key)
    if not source_spec or not target_spec or not str(source_id or '').isdigit() or not str(target_id or '').isdigit() or (source_key == target_key and source_id == target_id):
        messages.error(request, 'Select a valid related QMS record before linking.')
        return redirect(request.META.get('HTTP_REFERER', 'dashboards:head_qa_dashboard'))
    source = get_object_or_404(source_spec[0], pk=source_id)
    target = get_object_or_404(target_spec[0], pk=target_id)
    from_type = ContentType.objects.get_for_model(source, for_concrete_model=False)
    to_type = ContentType.objects.get_for_model(target, for_concrete_model=False)
    link, created = QMSRecordLink.objects.get_or_create(
        from_content_type=from_type, from_object_id=source.pk,
        to_content_type=to_type, to_object_id=target.pk,
        link_type=request.POST.get('link_type', 'related'),
        defaults={'rationale': request.POST.get('rationale', '').strip(), 'created_by': request.user},
    )
    if not created and request.POST.get('rationale'):
        link.rationale = request.POST.get('rationale', '').strip()
        link.save(update_fields=['rationale'])
    QMSFieldAuditTrail.objects.create(
        model_name=source.__class__.__name__, object_id=source.pk, field_name='qms_record_link',
        old_value='', new_value=_qms_record_label(target), reason='Cross-module QMS relationship created',
        changed_by=request.user,
    )
    messages.success(request, 'QMS records linked successfully.' if created else 'QMS relationship already exists.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboards:head_qa_dashboard'))


@login_required
@require_POST
def qms_record_link_delete(request, link_id):
    link = get_object_or_404(QMSRecordLink, pk=link_id)
    link.delete()
    messages.success(request, 'QMS relationship removed.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboards:head_qa_dashboard'))


# ============================================================================
# QMS ACTION DETAIL VIEW (Change Control, CAPA, etc.)
# ============================================================================

@login_required
def qms_action_detail(request, action_id):
    """View full QMS Action with attachments, comments, and activity log"""
    action = get_object_or_404(QMSAction.objects.select_related('created_by', 'assigned_to'), pk=action_id)
    
    # Get related data
    attachments = action.attachments.all().select_related('uploaded_by')
    comments = action.comments.all().select_related('user')
    activity_log = action.activity_log.all().select_related('user')[:50]  # Last 50 activities
    
    # Handle POST for status/details update
    if request.method == 'POST':
        if 'update_status' in request.POST:
            old_status = action.status
            new_status = request.POST.get('status')
            
            if new_status and new_status != old_status:
                action.status = new_status
                action.save()
                
                # Log activity
                QMSActivityLog.objects.create(
                    qms_action=action,
                    action_type='status_changed',
                    field_changed='status',
                    old_value=old_status,
                    new_value=new_status,
                    description=f'Status changed from {old_status} to {new_status}',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Status updated to {action.get_status_display()}')
            
            return redirect('dashboards:qms_action_detail', action_id=action.id)
    
    context = {
        'action': action,
        'attachments': attachments,
        'comments': comments,
        'activity_log': activity_log,
        'page_title': f'{action.qms_number} - {action.title}',
    }
    context.update(_qms_relationship_context(action, 'action'))
    
    return render(request, 'dashboards/qms/action_detail.html', context)


@login_required
def qms_capa_detail(request, capa_id):
    """Full CAPA lifecycle workspace with guarded review and closure."""
    capa = get_object_or_404(
        QMSCAPA.objects.select_related(
            'qms_action__created_by', 'qms_action__assigned_to', 'source_deviation',
            'source_audit', 'action_owner', 'qa_reviewer', 'approved_by',
            'effectiveness_verified_by', 'closed_by', 'created_by'
        ),
        pk=capa_id,
    )
    action = capa.qms_action
    attachments = action.attachments.all().select_related('uploaded_by')
    comments = action.comments.all().select_related('user')
    activity_log = action.activity_log.all().select_related('user')[:100]

    if request.method == 'POST':
        operation = request.POST.get('capa_operation', 'save')
        is_qa_reviewer = request.user.is_staff or getattr(request.user, 'role', None) in {'qa', 'head_qa', 'admin'}
        if operation in {'approve', 'verify_effectiveness', 'close'} and not is_qa_reviewer:
            messages.error(request, 'Only QA reviewers can approve, verify, or close a CAPA.')
            return redirect('dashboards:qms_capa_detail', capa_id=capa.id)
        if operation in {'approve', 'verify_effectiveness', 'close'} and not verify_signature_reauthentication(request):
            messages.error(request, 'Password re-authentication is required for this CAPA decision.')
            return redirect('dashboards:qms_capa_detail', capa_id=capa.id)
        before = {field: getattr(capa, field) for field in (
            'status', 'priority', 'problem_statement', 'containment_action',
            'root_cause_method', 'root_cause_analysis', 'corrective_action_plan',
            'preventive_action_plan', 'action_owner_id', 'target_completion_date',
            'effectiveness_method', 'effectiveness_criteria', 'effectiveness_result',
            'effectiveness_evidence', 'effectiveness_review_date', 'closure_justification',
            'source_type', 'source_reference',
        )}

        for field in ('problem_statement', 'containment_action', 'root_cause_method',
                      'root_cause_analysis', 'corrective_action_plan', 'preventive_action_plan',
                      'effectiveness_method', 'effectiveness_criteria', 'effectiveness_result',
                      'effectiveness_evidence', 'closure_justification', 'source_reference'):
            if field in request.POST:
                setattr(capa, field, request.POST.get(field, '').strip())
        if 'priority' in request.POST:
            capa.priority = request.POST.get('priority')
        if 'source_type' in request.POST:
            capa.source_type = request.POST.get('source_type')
        if 'source_deviation' in request.POST:
            capa.source_deviation_id = request.POST.get('source_deviation') or None
        if 'source_audit' in request.POST:
            capa.source_audit_id = request.POST.get('source_audit') or None
        if capa.source_deviation_id:
            capa.source_type = 'deviation'
            capa.source_audit_id = None
        elif capa.source_audit_id:
            capa.source_type = 'audit'
            capa.source_deviation_id = None
        if 'action_owner' in request.POST:
            capa.action_owner_id = request.POST.get('action_owner') or None
        if 'target_completion_date' in request.POST:
            capa.target_completion_date = parse_date(request.POST.get('target_completion_date') or '')
        if 'effectiveness_review_date' in request.POST:
            capa.effectiveness_review_date = parse_date(request.POST.get('effectiveness_review_date') or '')

        if operation == 'submit_review':
            if not capa.has_source_link:
                messages.error(request, 'Link this CAPA to a deviation, audit finding, or source reference before review.')
                return redirect('dashboards:qms_capa_detail', capa_id=capa.id)
            required = [capa.problem_statement, capa.root_cause_analysis,
                        capa.corrective_action_plan, capa.preventive_action_plan]
            if not all(value.strip() for value in required):
                messages.error(request, 'Complete the problem statement, root cause, corrective action, and preventive action before review.')
                return redirect('dashboards:qms_capa_detail', capa_id=capa.id)
            capa.status = 'effectiveness_review'
            capa.qa_reviewer = request.user
            action.status = 'pending_approval'
            route, _ = QMSApprovalRoute.objects.get_or_create(
                target_model='QMSCAPA',
                target_object_id=capa.id,
                defaults={'title': f'{capa.capa_number} QA approval', 'created_by': request.user, 'status': 'in_review'},
            )
            route.status = 'in_review'
            route.save(update_fields=['status', 'updated_at'])
            QMSApprovalStep.objects.get_or_create(
                route=route,
                sequence=1,
                defaults={'role': 'QA Reviewer', 'assigned_to': request.user},
            )
        elif operation == 'approve':
            if capa.status not in ('effectiveness_review', 'action_plan', 'implementation'):
                messages.error(request, 'CAPA must be in review before it can be approved.')
                return redirect('dashboards:qms_capa_detail', capa_id=capa.id)
            if capa.created_by_id == request.user.id and not request.user.is_staff:
                messages.error(request, 'The CAPA creator cannot be the sole approving reviewer.')
                return redirect('dashboards:qms_capa_detail', capa_id=capa.id)
            capa.approved_by = request.user
            capa.approved_at = timezone.now()
            capa.status = 'effectiveness_review'
            action.status = 'action_required'
            route = QMSApprovalRoute.objects.filter(target_model='QMSCAPA', target_object_id=capa.id).first()
            if route:
                route.status = 'approved'
                route.save(update_fields=['status', 'updated_at'])
                QMSApprovalStep.objects.filter(route=route, sequence=1).update(
                    decision='approved', signed_by=request.user, signed_at=timezone.now()
                )
            if not QMSElectronicSignature.objects.filter(target_model='QMSCAPA', target_object_id=capa.id, meaning='CAPA approval').exists():
                QMSElectronicSignature.objects.create(
                    target_model='QMSCAPA', target_object_id=capa.id, meaning='CAPA approval',
                    signer=request.user, ip_address=request.META.get('REMOTE_ADDR'),
                    reauthenticated=True, reauthenticated_at=timezone.now(),
                )
        elif operation == 'verify_effectiveness':
            if capa.effectiveness_result != 'effective' or not capa.effectiveness_criteria.strip() or not capa.effectiveness_evidence.strip():
                messages.error(request, 'Record measurable acceptance criteria and effective evidence before verification.')
                return redirect('dashboards:qms_capa_detail', capa_id=capa.id)
            capa.effectiveness_verified_by = request.user
            capa.effectiveness_review_date = capa.effectiveness_review_date or timezone.now().date()
            capa.status = 'effectiveness_review'
        elif operation == 'close':
            if not capa.is_ready_for_closure:
                messages.error(request, 'CAPA cannot be closed until actions, effective results, evidence, and QA approval are complete.')
                return redirect('dashboards:qms_capa_detail', capa_id=capa.id)
            capa.status = 'closed'
            capa.closed_by = request.user
            capa.closed_at = timezone.now()
            action.status = 'closed'
            action.closed_at = timezone.now()
            action.approved_by = request.user
            if not QMSElectronicSignature.objects.filter(target_model='QMSCAPA', target_object_id=capa.id, meaning='CAPA closure').exists():
                QMSElectronicSignature.objects.create(
                    target_model='QMSCAPA', target_object_id=capa.id, meaning='CAPA closure',
                    signer=request.user, ip_address=request.META.get('REMOTE_ADDR'),
                    reauthenticated=True, reauthenticated_at=timezone.now(),
                )
        elif operation == 'cancel':
            capa.status = 'cancelled'
            action.status = 'cancelled'
        else:
            capa.status = request.POST.get('status', capa.status)
            action.status = 'closed' if capa.status == 'closed' else ('pending_approval' if capa.status == 'effectiveness_review' else 'action_required')

        capa.save()
        action.priority = capa.priority
        action.root_cause = capa.root_cause_analysis
        action.corrective_action = capa.corrective_action_plan
        action.preventive_action = capa.preventive_action_plan
        action.effectiveness_check = capa.effectiveness_evidence
        action.save()

        changed = []
        for field, old_value in before.items():
            new_value = getattr(capa, field)
            if str(old_value or '') != str(new_value or ''):
                changed.append(field)
                QMSFieldAuditTrail.objects.create(
                    model_name='QMSCAPA',
                    object_id=capa.id,
                    field_name=field,
                    old_value=str(old_value or ''),
                    new_value=str(new_value or ''),
                    reason=f'CAPA workflow: {operation}',
                    changed_by=request.user,
                )
        description = f'CAPA {capa.capa_number} {operation.replace("_", " ")}'
        if changed:
            description += f'; updated: {", ".join(changed)}'
        QMSActivityLog.objects.create(
            qms_action=action,
            action_type='approved' if operation == 'approve' else ('status_changed' if operation != 'save' else 'updated'),
            field_changed='capa_workflow',
            new_value=capa.status,
            description=description,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        messages.success(request, f'{capa.capa_number} updated.')
        return redirect('dashboards:qms_capa_detail', capa_id=capa.id)

    context = {
        'capa': capa,
        'action': action,
        'attachments': attachments,
        'comments': comments,
        'activity_log': activity_log,
        'users': get_user_model().objects.filter(is_active=True).order_by('username'),
        'deviations': QMSDeviation.objects.order_by('-created_at')[:100],
        'audits': QMSAudit.objects.order_by('-created_at')[:100],
        'approval_route': QMSApprovalRoute.objects.filter(target_model='QMSCAPA', target_object_id=capa.id).prefetch_related('steps').first(),
        'page_title': f'{capa.capa_number} - CAPA',
    }
    context.update(_qms_relationship_context(capa, 'capa'))
    return render(request, 'dashboards/qms/capa_detail.html', context)


@login_required
def qms_change_control_detail(request, change_id):
    """Full Change Control workflow with impact, approval, implementation, and effectiveness gates."""
    change = get_object_or_404(
        QMSChangeControl.objects.select_related(
            'qms_action__created_by', 'qms_action__assigned_to', 'owner',
            'implementation_owner', 'qa_reviewer', 'approved_by',
            'effectiveness_verified_by', 'closed_by', 'created_by'
        ),
        pk=change_id,
    )
    action = change.qms_action
    attachments = action.attachments.all().select_related('uploaded_by')
    comments = action.comments.all().select_related('user')
    activity_log = action.activity_log.all().select_related('user')[:100]

    if request.method == 'POST':
        operation = request.POST.get('change_operation', 'save')
        is_qa = request.user.is_staff or getattr(request.user, 'role', None) in {'qa', 'head_qa', 'admin'}
        if operation in {'approve', 'verify_effectiveness', 'close'} and not is_qa:
            messages.error(request, 'Only QA reviewers can approve, verify, or close a Change Control.')
            return redirect('dashboards:qms_change_control_detail', change_id=change.id)
        if operation in {'approve', 'verify_effectiveness', 'close'} and not verify_signature_reauthentication(request):
            messages.error(request, 'Password re-authentication is required for this Change Control decision.')
            return redirect('dashboards:qms_change_control_detail', change_id=change.id)

        tracked_fields = (
            'change_type', 'risk_level', 'source_reference', 'justification', 'current_state',
            'proposed_state', 'quality_impact', 'gmp_impact', 'validation_impact',
            'regulatory_impact', 'documentation_impact', 'training_impact', 'stability_impact',
            'inventory_impact', 'impact_summary', 'qa_impact_decision', 'implementation_plan',
            'implementation_notes', 'affected_documents', 'training_plan', 'validation_plan',
            'implementation_owner_id', 'planned_implementation_date', 'actual_implementation_date',
            'effectiveness_method', 'effectiveness_criteria', 'effectiveness_result',
            'effectiveness_evidence', 'effectiveness_review_date',
        )
        before = {field: getattr(change, field) for field in tracked_fields}
        text_fields = (
            'source_reference', 'justification', 'current_state', 'proposed_state', 'impact_summary',
            'qa_impact_decision', 'implementation_plan', 'implementation_notes', 'affected_documents',
            'training_plan', 'validation_plan', 'effectiveness_method', 'effectiveness_criteria',
            'effectiveness_result', 'effectiveness_evidence',
        )
        for field in text_fields:
            if field in request.POST:
                setattr(change, field, request.POST.get(field, '').strip())
        for field in ('change_type', 'risk_level'):
            if field in request.POST:
                setattr(change, field, request.POST.get(field))
        for field in ('quality_impact', 'gmp_impact', 'validation_impact', 'regulatory_impact',
                      'documentation_impact', 'training_impact', 'stability_impact', 'inventory_impact'):
            # Checkbox inputs are omitted when unchecked; always persist the submitted state.
            setattr(change, field, request.POST.get(field) in ('1', 'true', 'on', 'yes'))
        if 'owner' in request.POST:
            change.owner_id = request.POST.get('owner') or None
        if 'implementation_owner' in request.POST:
            change.implementation_owner_id = request.POST.get('implementation_owner') or None
        for field in ('planned_implementation_date', 'actual_implementation_date', 'effectiveness_review_date'):
            if field in request.POST:
                setattr(change, field, parse_date(request.POST.get(field) or ''))

        if operation == 'submit_review':
            if not change.ready_for_approval:
                messages.error(request, 'Complete justification, proposed state, impact assessment, and owner before QA review.')
                return redirect('dashboards:qms_change_control_detail', change_id=change.id)
            change.status = 'qa_review'
            change.qa_reviewer = request.user
            action.status = 'pending_approval'
            route, _ = QMSApprovalRoute.objects.get_or_create(
                target_model='QMSChangeControl', target_object_id=change.id,
                defaults={'title': f'{change.change_number} QA approval', 'created_by': request.user, 'status': 'in_review'},
            )
            route.status = 'in_review'
            route.save(update_fields=['status', 'updated_at'])
            QMSApprovalStep.objects.get_or_create(route=route, sequence=1, defaults={'role': 'QA Reviewer', 'assigned_to': request.user})
        elif operation == 'approve':
            if not change.ready_for_approval or change.status != 'qa_review':
                messages.error(request, 'Change Control is not ready for approval.')
                return redirect('dashboards:qms_change_control_detail', change_id=change.id)
            if change.created_by_id == request.user.id and not request.user.is_staff:
                messages.error(request, 'The Change Control creator cannot be the sole approving reviewer.')
                return redirect('dashboards:qms_change_control_detail', change_id=change.id)
            change.approved_by = request.user
            change.approved_at = timezone.now()
            change.status = 'approved'
            action.status = 'action_required'
            route = QMSApprovalRoute.objects.filter(target_model='QMSChangeControl', target_object_id=change.id).first()
            if route:
                route.status = 'approved'
                route.save(update_fields=['status', 'updated_at'])
                QMSApprovalStep.objects.filter(route=route, sequence=1).update(decision='approved', signed_by=request.user, signed_at=timezone.now())
            if not QMSElectronicSignature.objects.filter(target_model='QMSChangeControl', target_object_id=change.id, meaning='Change Control approval').exists():
                QMSElectronicSignature.objects.create(target_model='QMSChangeControl', target_object_id=change.id, meaning='Change Control approval', signer=request.user, ip_address=request.META.get('REMOTE_ADDR'), reauthenticated=True, reauthenticated_at=timezone.now())
        elif operation == 'start_implementation':
            if not change.approved_by_id:
                messages.error(request, 'Change Control must be approved before implementation starts.')
                return redirect('dashboards:qms_change_control_detail', change_id=change.id)
            change.status = 'implementation'
            action.status = 'action_required'
        elif operation == 'verify_effectiveness':
            if change.effectiveness_result != 'effective' or not change.effectiveness_criteria.strip() or not change.effectiveness_evidence.strip() or not change.actual_implementation_date:
                messages.error(request, 'Record implementation completion, acceptance criteria, and effective evidence before verification.')
                return redirect('dashboards:qms_change_control_detail', change_id=change.id)
            change.effectiveness_verified_by = request.user
            change.effectiveness_review_date = change.effectiveness_review_date or timezone.now().date()
            change.status = 'effectiveness_review'
        elif operation == 'close':
            if not change.ready_for_closure:
                messages.error(request, 'Change Control cannot be closed until implementation, effectiveness, evidence, verification, and QA approval are complete.')
                return redirect('dashboards:qms_change_control_detail', change_id=change.id)
            change.status = 'closed'
            change.closed_by = request.user
            change.closed_at = timezone.now()
            action.status = 'closed'
            action.closed_at = timezone.now()
            action.approved_by = request.user
            if not QMSElectronicSignature.objects.filter(target_model='QMSChangeControl', target_object_id=change.id, meaning='Change Control closure').exists():
                QMSElectronicSignature.objects.create(target_model='QMSChangeControl', target_object_id=change.id, meaning='Change Control closure', signer=request.user, ip_address=request.META.get('REMOTE_ADDR'), reauthenticated=True, reauthenticated_at=timezone.now())
        elif operation == 'cancel':
            change.status = 'cancelled'
            action.status = 'cancelled'
        else:
            change.status = request.POST.get('status', change.status)
            action.status = 'pending_approval' if change.status == 'qa_review' else ('closed' if change.status == 'closed' else 'action_required')

        change.save()
        action.priority = change.risk_level
        action.save()
        changed = []
        for field, old_value in before.items():
            new_value = getattr(change, field)
            if str(old_value or '') != str(new_value or ''):
                changed.append(field)
                QMSFieldAuditTrail.objects.create(
                    model_name='QMSChangeControl', object_id=change.id, field_name=field,
                    old_value=str(old_value or ''), new_value=str(new_value or ''),
                    reason=f'Change Control workflow: {operation}', changed_by=request.user,
                )
        QMSActivityLog.objects.create(
            qms_action=action,
            action_type='approved' if operation == 'approve' else ('status_changed' if operation != 'save' else 'updated'),
            field_changed='change_control_workflow', new_value=change.status,
            description=f'{change.change_number} {operation.replace("_", " ")}; updated: {", ".join(changed) or "none"}',
            user=request.user, ip_address=request.META.get('REMOTE_ADDR'),
        )
        messages.success(request, f'{change.change_number} updated.')
        return redirect('dashboards:qms_change_control_detail', change_id=change.id)

    return render(request, 'dashboards/qms/change_control_detail.html', {
        'change': change, 'action': action, 'attachments': attachments,
        'comments': comments, 'activity_log': activity_log,
        'users': get_user_model().objects.filter(is_active=True).order_by('username'),
        'approval_route': QMSApprovalRoute.objects.filter(target_model='QMSChangeControl', target_object_id=change.id).prefetch_related('steps').first(),
        'page_title': f'{change.change_number} - Change Control',
        **_qms_relationship_context(change, 'change_control'),
    })


@login_required
@require_POST
def qms_action_upload_file(request, action_id):
    """Upload file attachment to QMS Action"""
    action = get_object_or_404(QMSAction, pk=action_id)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    
    uploaded_file = request.FILES['file']
    description = request.POST.get('description', '')
    if request.POST.get('is_controlled') in {'1', 'true', 'yes', 'on'}:
        document.controlled_file = uploaded_file
        document.save(update_fields=['controlled_file', 'updated_at'])
    
    # Create attachment
    attachment = QMSAttachment.objects.create(
        qms_action=action,
        file=uploaded_file,
        description=description,
        uploaded_by=request.user
    )
    
    # Log activity
    QMSActivityLog.objects.create(
        qms_action=action,
        action_type='file_uploaded',
        description=f'Uploaded file: {attachment.filename}',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'uploaded_by': attachment.uploaded_by.username,
            'uploaded_at': attachment.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
@require_POST
def qms_action_add_comment(request, action_id):
    """Add comment to QMS Action"""
    action = get_object_or_404(QMSAction, pk=action_id)
    
    comment_text = request.POST.get('comment', '').strip()
    if not comment_text:
        return JsonResponse({'success': False, 'error': 'Comment cannot be empty'}, status=400)
    
    is_internal = request.POST.get('is_internal') == '1'
    
    # Create comment
    comment = QMSComment.objects.create(
        qms_action=action,
        comment_text=comment_text,
        user=request.user,
        is_internal=is_internal
    )
    
    # Log activity
    QMSActivityLog.objects.create(
        qms_action=action,
        action_type='comment_added',
        description=f'Added comment: {comment_text[:50]}...' if len(comment_text) > 50 else f'Added comment: {comment_text}',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'comment_text': comment.comment_text,
            'user': comment.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_internal': comment.is_internal,
        }
    })


# ============================================================================
# QMS AUDIT DETAIL VIEW
# ============================================================================

@login_required
def qms_audit_detail(request, audit_id):
    """View full Audit with attachments, comments, and activity log"""
    audit = get_object_or_404(QMSAudit.objects.select_related('created_by'), pk=audit_id)
    
    attachments = audit.attachments.all().select_related('uploaded_by')
    comments = audit.comments.all().select_related('user')
    activity_log = audit.activity_log.all().select_related('user')[:50]
    
    if request.method == 'POST':
        if 'update_status' in request.POST:
            old_status = audit.status
            new_status = request.POST.get('status')
            
            if new_status and new_status != old_status:
                audit.status = new_status
                audit.save()
                
                QMSActivityLog.objects.create(
                    qms_audit=audit,
                    action_type='status_changed',
                    field_changed='status',
                    old_value=old_status,
                    new_value=new_status,
                    description=f'Status changed from {old_status} to {new_status}',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Status updated to {audit.get_status_display()}')
            
            return redirect('dashboards:qms_audit_detail', audit_id=audit.id)
    
    context = {
        'audit': audit,
        'attachments': attachments,
        'comments': comments,
        'activity_log': activity_log,
        'page_title': f'{audit.audit_number} - {audit.title}',
        **_qms_relationship_context(audit, 'audit'),
    }
    
    return render(request, 'dashboards/qms/audit_detail.html', context)


@login_required
@require_POST
def qms_audit_upload_file(request, audit_id):
    """Upload file to Audit"""
    audit = get_object_or_404(QMSAudit, pk=audit_id)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    
    uploaded_file = request.FILES['file']
    description = request.POST.get('description', '')
    
    attachment = QMSAttachment.objects.create(
        qms_audit=audit,
        file=uploaded_file,
        description=description,
        uploaded_by=request.user
    )
    
    QMSActivityLog.objects.create(
        qms_audit=audit,
        action_type='file_uploaded',
        description=f'Uploaded file: {attachment.filename}',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'uploaded_by': attachment.uploaded_by.username,
            'uploaded_at': attachment.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
@require_POST
def qms_audit_add_comment(request, audit_id):
    """Add comment to Audit"""
    audit = get_object_or_404(QMSAudit, pk=audit_id)
    
    comment_text = request.POST.get('comment', '').strip()
    if not comment_text:
        return JsonResponse({'success': False, 'error': 'Comment cannot be empty'}, status=400)
    
    is_internal = request.POST.get('is_internal') == '1'
    
    comment = QMSComment.objects.create(
        qms_audit=audit,
        comment_text=comment_text,
        user=request.user,
        is_internal=is_internal
    )
    
    QMSActivityLog.objects.create(
        qms_audit=audit,
        action_type='comment_added',
        description=f'Added comment',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'comment_text': comment.comment_text,
            'user': comment.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_internal': comment.is_internal,
        }
    })


# ============================================================================
# QMS RISK ASSESSMENT DETAIL VIEW
# ============================================================================

@login_required
def qms_risk_detail(request, risk_id):
    """View full Risk Assessment with attachments, comments, and activity log"""
    risk = get_object_or_404(QMSRiskAssessment.objects.select_related('owner'), pk=risk_id)
    
    attachments = risk.attachments.all().select_related('uploaded_by')
    comments = risk.comments.all().select_related('user')
    activity_log = risk.activity_log.all().select_related('user')[:50]
    
    if request.method == 'POST':
        if 'update_status' in request.POST:
            old_status = risk.status
            new_status = request.POST.get('status')
            
            if new_status and new_status != old_status:
                risk.status = new_status
                risk.save()
                
                QMSActivityLog.objects.create(
                    qms_risk=risk,
                    action_type='status_changed',
                    field_changed='status',
                    old_value=old_status,
                    new_value=new_status,
                    description=f'Status changed from {old_status} to {new_status}',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Status updated to {risk.get_status_display()}')
            
            return redirect('dashboards:qms_risk_detail', risk_id=risk.id)
    
    context = {
        'risk': risk,
        'attachments': attachments,
        'comments': comments,
        'activity_log': activity_log,
        # Keep arithmetic out of the template.  RPN is normally positive,
        # but retain a safe fallback for legacy or manually imported records.
        'risk_reduction_percent': round(
            ((risk.rpn - risk.residual_rpn) / risk.rpn) * 100, 1
        ) if risk.rpn else 0,
        'page_title': f'{risk.risk_number} - {risk.title}',
        **_qms_relationship_context(risk, 'risk'),
    }
    
    return render(request, 'dashboards/qms/risk_detail.html', context)


@login_required
@require_POST
def qms_risk_upload_file(request, risk_id):
    """Upload file to Risk Assessment"""
    risk = get_object_or_404(QMSRiskAssessment, pk=risk_id)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    
    uploaded_file = request.FILES['file']
    description = request.POST.get('description', '')
    
    attachment = QMSAttachment.objects.create(
        qms_risk=risk,
        file=uploaded_file,
        description=description,
        uploaded_by=request.user
    )
    
    QMSActivityLog.objects.create(
        qms_risk=risk,
        action_type='file_uploaded',
        description=f'Uploaded file: {attachment.filename}',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'uploaded_by': attachment.uploaded_by.username,
            'uploaded_at': attachment.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
@require_POST
def qms_risk_add_comment(request, risk_id):
    """Add comment to Risk Assessment"""
    risk = get_object_or_404(QMSRiskAssessment, pk=risk_id)
    
    comment_text = request.POST.get('comment', '').strip()
    if not comment_text:
        return JsonResponse({'success': False, 'error': 'Comment cannot be empty'}, status=400)
    
    is_internal = request.POST.get('is_internal') == '1'
    
    comment = QMSComment.objects.create(
        qms_risk=risk,
        comment_text=comment_text,
        user=request.user,
        is_internal=is_internal
    )
    
    QMSActivityLog.objects.create(
        qms_risk=risk,
        action_type='comment_added',
        description=f'Added comment',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'comment_text': comment.comment_text,
            'user': comment.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_internal': comment.is_internal,
        }
    })


# ============================================================================
# QMS DOCUMENT DETAIL VIEW
# ============================================================================

@login_required
def qms_document_detail(request, document_id):
    """View full Document with attachments, comments, and activity log"""
    document = get_object_or_404(QMSDocument.objects.select_related('owner', 'prepared_by', 'reviewed_by', 'approved_by'), pk=document_id)
    
    attachments = document.attachments.all().select_related('uploaded_by')
    comments = document.comments.all().select_related('user')
    activity_log = document.activity_log.all().select_related('user')[:50]
    
    if request.method == 'POST':
        operation = request.POST.get('document_operation', 'save')
        if operation == 'approve' and not verify_signature_reauthentication(request):
            messages.error(request, 'Password re-authentication is required before approving a controlled document.')
            return redirect('dashboards:qms_document_detail', document_id=document.id)
        is_qa = request.user.is_staff or getattr(request.user, 'role', None) in {'qa', 'head_qa', 'admin'}
        if operation in {'approve', 'make_effective', 'obsolete', 'archive'} and not is_qa:
            messages.error(request, 'Only QA reviewers can approve, effective-date, obsolete, or archive controlled documents.')
            return redirect('dashboards:qms_document_detail', document_id=document.id)
        old_status = document.status
        for field in ('document_type', 'title', 'version', 'document_summary', 'revision_reason', 'change_control_reference',
                      'supersedes_version', 'review_comments', 'approval_notes'):
            if field in request.POST:
                setattr(document, field, request.POST.get(field, '').strip())
        for field in ('effective_date', 'expiry_date', 'revision_date', 'next_review_date'):
            if field in request.POST:
                setattr(document, field, parse_date(request.POST.get(field) or ''))
        if 'owner' in request.POST:
            document.owner_id = request.POST.get('owner') or None
        if 'reviewed_by' in request.POST:
            document.reviewed_by_id = request.POST.get('reviewed_by') or None
        if operation == 'submit_review':
            if not document.ready_for_review:
                messages.error(request, 'Add the controlled file, owner, version, and document details before review.')
                return redirect('dashboards:qms_document_detail', document_id=document.id)
            document.status = 'in_review'
        elif operation == 'approve':
            if not document.controlled_file:
                messages.error(request, 'Upload the controlled document file before approval.')
                return redirect('dashboards:qms_document_detail', document_id=document.id)
            if document.status != 'in_review' or not document.ready_for_approval:
                messages.error(request, 'Document review comments and reviewer assignment are required before approval.')
                return redirect('dashboards:qms_document_detail', document_id=document.id)
            if document.reviewed_by_id == request.user.id and not request.user.is_staff:
                messages.error(request, 'The document reviewer cannot also be the approving QA signer.')
                return redirect('dashboards:qms_document_detail', document_id=document.id)
            document.approved_by = request.user
            document.signed_at = timezone.now()
            document.electronic_signature = f'{request.user.get_username()} approved {document.document_number}'
            document.status = 'approved'
            QMSElectronicSignature.objects.create(target_model='QMSDocument', target_object_id=document.id, meaning='Document approval', signer=request.user, ip_address=request.META.get('REMOTE_ADDR'), reauthenticated=True, reauthenticated_at=timezone.now())
        elif operation == 'make_effective':
            if document.status != 'approved' or not document.ready_for_effective:
                messages.error(request, 'Approve the document and set an effective date before making it effective.')
                return redirect('dashboards:qms_document_detail', document_id=document.id)
            document.status = 'effective'
        elif operation == 'obsolete':
            document.status = 'obsolete'
        elif operation == 'archive':
            document.status = 'archived'
        else:
            requested_status = request.POST.get('status', document.status)
            if requested_status == 'approved' and not document.controlled_file:
                messages.error(request, 'Upload the controlled document file before approval.')
                return redirect('dashboards:qms_document_detail', document_id=document.id)
            document.status = requested_status
        document.save()
        if old_status != document.status:
            QMSFieldAuditTrail.objects.create(model_name='QMSDocument', object_id=document.id, field_name='status', old_value=old_status, new_value=document.status, reason=f'Document workflow: {operation}', changed_by=request.user)
            QMSActivityLog.objects.create(qms_document=document, action_type='status_changed', field_changed='status', old_value=old_status, new_value=document.status, description=f'Document workflow: {operation.replace("_", " ")}', user=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f'{document.document_number} updated.')
        return redirect('dashboards:qms_document_detail', document_id=document.id)
    
    context = {
        'document': document,
        'attachments': attachments,
        'comments': comments,
        'activity_log': activity_log,
        'users': get_user_model().objects.filter(is_active=True).order_by('username'),
        'page_title': f'{document.document_number} - {document.title}',
        **_qms_relationship_context(document, 'document'),
    }
    
    return render(request, 'dashboards/qms/document_detail.html', context)


@login_required
def qms_calibration_detail(request, calibration_id):
    """Controlled calibration asset, event, evidence, verification, and traceability workspace."""
    calibration = get_object_or_404(
        QMSCalibrationRecord.objects.select_related('owner', 'created_by', 'verified_by').prefetch_related('events'),
        pk=calibration_id,
    )
    events = calibration.events.select_related('performed_by', 'verified_by').all()
    activity_log = calibration.activity_log.select_related('user').all()[:100]
    comments = calibration.comments.select_related('user').all()
    if request.method == 'POST':
        operation = request.POST.get('calibration_operation', 'save')
        is_qa = request.user.is_staff or getattr(request.user, 'role', None) in {'qa', 'head_qa', 'admin'}
        if operation == 'verify' and not is_qa:
            messages.error(request, 'Only QA users can verify calibration results.')
            return redirect('dashboards:qms_calibration_detail', calibration_id=calibration.id)
        old_status = calibration.status
        for field in ('equipment_id', 'equipment_name', 'department', 'manufacturer', 'model_number', 'serial_number', 'location', 'method_reference', 'acceptance_criteria', 'notes'):
            if field in request.POST:
                setattr(calibration, field, request.POST.get(field, '').strip())
        if 'calibration_interval_days' in request.POST:
            try:
                calibration.calibration_interval_days = max(1, int(request.POST.get('calibration_interval_days') or 365))
            except (TypeError, ValueError):
                messages.error(request, 'Calibration interval must be a positive number of days.')
                return redirect('dashboards:qms_calibration_detail', calibration_id=calibration.id)
        if 'owner' in request.POST:
            calibration.owner_id = request.POST.get('owner') or None
        if 'certificate_file' in request.FILES:
            calibration.certificate_file = request.FILES['certificate_file']
        if operation == 'record_calibration':
            calibration_date = parse_date(request.POST.get('calibration_date') or '')
            if not calibration_date:
                messages.error(request, 'Calibration date is required.')
                return redirect('dashboards:qms_calibration_detail', calibration_id=calibration.id)
            result = request.POST.get('result', 'pass')
            if result not in {'pass', 'fail', 'conditional'}:
                result = 'fail'
            if result in {'pass', 'conditional'} and not request.FILES.get('event_certificate_file') and not calibration.certificate_file:
                messages.error(request, 'Upload a calibration certificate before recording a passing result.')
                return redirect('dashboards:qms_calibration_detail', calibration_id=calibration.id)
            next_due = parse_date(request.POST.get('event_next_due_date') or '')
            if not next_due and result == 'pass':
                next_due = calibration_date + timedelta(days=calibration.calibration_interval_days)
            event = QMSCalibrationEvent.objects.create(
                calibration=calibration, calibration_date=calibration_date, result=result,
                certificate_number=request.POST.get('certificate_number', '').strip(),
                certificate_file=request.FILES.get('event_certificate_file'), next_due_date=next_due,
                performed_by=request.user, notes=request.POST.get('event_notes', '').strip(),
            )
            calibration.last_calibrated = calibration_date
            calibration.next_due_date = next_due
            calibration.status = 'out_of_service' if result == 'fail' else ('due' if next_due and next_due <= timezone.now().date() + timedelta(days=30) else 'in_service')
            if request.FILES.get('event_certificate_file') and not calibration.certificate_file:
                calibration.certificate_file = request.FILES['event_certificate_file']
            operation_description = f'Calibration event recorded: {event.get_result_display()}'
        elif operation == 'verify':
            event = events.first()
            if not event or event.result == 'fail' or (event.result in {'pass', 'conditional'} and not event.certificate_file and not calibration.certificate_file):
                messages.error(request, 'A passing calibration event with a certificate is required before QA verification.')
                return redirect('dashboards:qms_calibration_detail', calibration_id=calibration.id)
            event.verified_by = request.user
            event.verified_at = timezone.now()
            event.save(update_fields=['verified_by', 'verified_at'])
            calibration.verified_by = request.user
            calibration.verified_at = timezone.now()
            operation_description = 'Calibration result verified by QA'
            QMSElectronicSignature.objects.create(target_model='QMSCalibrationRecord', target_object_id=calibration.id, meaning='Calibration result verified', signer=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        else:
            requested_status = request.POST.get('status')
            if requested_status in dict(QMSCalibrationRecord.STATUS_CHOICES):
                calibration.status = requested_status
            elif calibration.status != 'out_of_service':
                calibration.status = calibration.calculated_status
            operation_description = 'Calibration record updated'
        calibration.save()
        if old_status != calibration.status:
            QMSFieldAuditTrail.objects.create(model_name='QMSCalibrationRecord', object_id=calibration.id, field_name='status', old_value=old_status, new_value=calibration.status, reason=operation_description, changed_by=request.user)
        QMSActivityLog.objects.create(qms_calibration=calibration, action_type='approved' if operation == 'verify' else ('status_changed' if old_status != calibration.status else 'updated'), field_changed='calibration_workflow', old_value=old_status, new_value=calibration.status, description=operation_description, user=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, 'Calibration record updated.')
        return redirect('dashboards:qms_calibration_detail', calibration_id=calibration.id)
    return render(request, 'dashboards/qms/calibration_detail.html', {
        'calibration': calibration, 'events': events, 'activity_log': activity_log, 'comments': comments,
        'users': get_user_model().objects.filter(is_active=True).order_by('username'),
        'page_title': f'{calibration.equipment_id} - Calibration',
        **_qms_relationship_context(calibration, 'calibration'),
    })


@login_required
def qms_qc_register(request):
    """QC Enterprise register: create and open controlled QC records."""
    from bmr.models import BMR
    from products.models import Product

    if request.method == 'POST':
        record_type = request.POST.get('qc_record_type', '').strip()
        title = request.POST.get('title', '').strip()
        bmr = BMR.objects.filter(pk=request.POST.get('bmr_id')).first() if request.POST.get('bmr_id') else None
        product = Product.objects.filter(pk=request.POST.get('product_id')).first() if request.POST.get('product_id') else None
        if record_type == 'oos':
            record = QMSLabInvestigation.objects.create(
                event_type=request.POST.get('event_type', 'oos'), test_name=title or 'QC investigation',
                opened_by=request.user, bmr=bmr, product=product,
            )
            return redirect('dashboards:qms_lab_investigation_detail', investigation_id=record.id)
        if record_type == 'stability':
            record = QMSStabilitySchedule.objects.create(
                product=product, bmr=bmr, condition=request.POST.get('condition', 'long_term'),
                time_point=request.POST.get('time_point', 'Initial'),
                pull_date=parse_date(request.POST.get('pull_date') or '') or timezone.now().date(),
                protocol_reference=request.POST.get('protocol_reference', '').strip(),
                storage_condition=request.POST.get('storage_condition', '').strip(),
                owner=request.user, created_by=request.user,
            )
            return redirect('dashboards:qms_stability_detail', stability_id=record.id)
        if record_type == 'coa':
            record = QMSCOA.objects.create(bmr=bmr, product=product, market=request.POST.get('market', '').strip(), prepared_by=request.user)
            return redirect('dashboards:qms_coa_detail', coa_id=record.id)
        if record_type == 'material_qc':
            lot = request.POST.get('material_lot_number', '').strip()
            if not lot:
                lot = f'MAT-{timezone.now():%Y%m%d%H%M%S}'
            record = QMSMaterialQC.objects.create(
                material_lot_number=lot, material_name=title or 'Material QC sample', bmr=bmr,
                owner=request.user, received_date=timezone.now().date(),
            )
            return redirect('dashboards:qms_material_qc_detail', material_qc_id=record.id)
        if record_type == 'supplier_quality':
            record = QMSSupplierQualification.objects.create(
                supplier_name=title or 'New supplier qualification', supplier_code=request.POST.get('supplier_code', '').strip(),
                material_name=request.POST.get('material_name', '').strip(), owner=request.user,
            )
            return redirect('dashboards:qms_supplier_quality_detail', supplier_id=record.id)
        messages.error(request, 'Select a valid QC record type.')

    context = {
        'page_title': 'QC Enterprise | Controlled Quality Records',
        'bmr_options': BMR.objects.select_related('product').order_by('-id')[:100],
        'product_options': Product.objects.order_by('product_name')[:100],
        'oos_records': QMSLabInvestigation.objects.select_related('bmr', 'product').order_by('-opened_at')[:12],
        'stability_records': QMSStabilitySchedule.objects.select_related('bmr', 'product').order_by('pull_date')[:12],
        'coa_records': QMSCOA.objects.select_related('bmr', 'product', 'quality_lot').order_by('-created_at')[:12],
        'material_records': QMSMaterialQC.objects.select_related('bmr', 'supplier').order_by('-created_at')[:12],
        'supplier_records': QMSSupplierQualification.objects.order_by('supplier_name')[:12],
        'oos_count': QMSLabInvestigation.objects.exclude(status='closed').count(),
        'stability_count': QMSStabilitySchedule.objects.exclude(status='closed').count(),
        'coa_count': QMSCOA.objects.exclude(status__in=['approved', 'void']).count(),
        'material_count': QMSMaterialQC.objects.exclude(status__in=['approved', 'rejected']).count(),
        'supplier_count': QMSSupplierQualification.objects.exclude(status='disqualified').count(),
    }
    return render(request, 'dashboards/qms/qc_register.html', context)


def _qms_qc_workspace(request, record_type, record_id):
    specs = {
        'oos': (QMSLabInvestigation, 'investigation_id', 'investigation_number', 'investigation'),
        'stability': (QMSStabilitySchedule, 'stability_id', 'study_number', 'stability'),
        'coa': (QMSCOA, 'coa_id', 'coa_number', 'coa'),
        'material_qc': (QMSMaterialQC, 'material_qc_id', 'material_lot_number', 'material_qc'),
        'supplier_quality': (QMSSupplierQualification, 'supplier_id', 'supplier_code', 'supplier'),
    }
    model, _, _, variable = specs[record_type]
    record = get_object_or_404(model, pk=record_id)
    is_qa = request.user.is_staff or getattr(request.user, 'role', None) in {'qa', 'head_qa', 'admin'}
    if request.method == 'POST':
        operation = request.POST.get('qc_operation', 'save')
        old_status = getattr(record, 'status', '')
        if record_type == 'oos':
            for field in ('event_type', 'test_name', 'specification', 'result_value', 'trend_reference', 'analyst_review', 'instrument_review', 'method_review', 'sample_review', 'retest_result', 'root_cause', 'qa_conclusion', 'disposition'):
                if field in request.POST:
                    setattr(record, field, request.POST.get(field, '').strip())
            if operation == 'phase2':
                required = ('analyst_review', 'instrument_review', 'method_review', 'sample_review')
                if not all(getattr(record, field).strip() for field in required):
                    messages.error(request, 'Complete analyst, instrument, method, and sample review before Phase 2.')
                    return redirect('dashboards:qms_lab_investigation_detail', investigation_id=record.id)
                record.status = 'phase2_full_investigation'
            elif operation == 'submit_qa':
                if not record.root_cause.strip() or not record.qa_conclusion.strip():
                    messages.error(request, 'Root cause and investigation conclusion are required before QA review.')
                    return redirect('dashboards:qms_lab_investigation_detail', investigation_id=record.id)
                record.status = 'qa_review'
            elif operation == 'approve':
                if not is_qa:
                    messages.error(request, 'Only QA users can approve OOS investigations.')
                    return redirect('dashboards:qms_lab_investigation_detail', investigation_id=record.id)
                if record.status != 'qa_review' or record.disposition == 'pending':
                    messages.error(request, 'The investigation must be in QA Review with a disposition before approval.')
                    return redirect('dashboards:qms_lab_investigation_detail', investigation_id=record.id)
                record.qa_reviewer = request.user
                record.status = 'capa_required' if record.disposition == 'retest_required' else 'closed'
                record.closed_at = timezone.now() if record.status == 'closed' else None
        elif record_type == 'stability':
            for field in ('condition', 'time_point', 'chamber', 'protocol_reference', 'storage_condition', 'specification_reference', 'result_summary', 'qa_review_notes'):
                if field in request.POST:
                    setattr(record, field, request.POST.get(field, '').strip())
            if 'pull_date' in request.POST:
                record.pull_date = parse_date(request.POST.get('pull_date') or '')
            if operation == 'record_result':
                result = QMSStabilityResult.objects.create(schedule=record, test_name=request.POST.get('result_test_name', 'Stability test').strip(), result_value=request.POST.get('result_value', '').strip(), specification=request.POST.get('result_specification', '').strip(), passed=request.POST.get('result_passed') == 'true', test_date=parse_date(request.POST.get('result_test_date') or '') or timezone.now().date(), analyst=request.user, comments=request.POST.get('result_comments', '').strip())
                record.status = 'tested' if result.passed else 'failed'
            elif operation == 'submit_qa':
                if not record.results.exists() or not record.result_summary.strip():
                    messages.error(request, 'Record at least one stability result and summary before QA review.')
                    return redirect('dashboards:qms_stability_detail', stability_id=record.id)
                record.status = 'qa_review'
            elif operation == 'approve':
                if not is_qa or record.status != 'qa_review':
                    messages.error(request, 'Only QA can approve a stability study in QA Review.')
                    return redirect('dashboards:qms_stability_detail', stability_id=record.id)
                record.reviewed_by = request.user
                record.reviewed_at = timezone.now()
                record.status = 'reviewed'
        elif record_type == 'coa':
            for field in ('market', 'specification_reference', 'result_summary'):
                if field in request.POST:
                    setattr(record, field, request.POST.get(field, '').strip())
            if request.FILES.get('certificate_file'):
                record.certificate_file = request.FILES['certificate_file']
            if operation == 'prepare':
                if not record.result_summary.strip():
                    messages.error(request, 'Add the QC result summary before preparing the COA.')
                    return redirect('dashboards:qms_coa_detail', coa_id=record.id)
                record.prepared_by = request.user
                record.status = 'qc_prepared'
            elif operation == 'submit_qa':
                if record.status != 'qc_prepared' or not record.result_summary.strip():
                    messages.error(request, 'Prepare the COA with results before QA review.')
                    return redirect('dashboards:qms_coa_detail', coa_id=record.id)
                record.qa_reviewer = request.user
                record.status = 'qa_review'
            elif operation == 'approve':
                if not is_qa or record.status != 'qa_review' or not record.certificate_file:
                    messages.error(request, 'QA approval requires QA Review status and a controlled COA file.')
                    return redirect('dashboards:qms_coa_detail', coa_id=record.id)
                record.approved_by = request.user
                record.approved_at = timezone.now()
                record.status = 'approved'
                QMSElectronicSignature.objects.create(target_model='QMSCOA', target_object_id=record.id, meaning='COA QA release', signer=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        elif record_type == 'material_qc':
            for field in ('material_name', 'material_code', 'result_summary', 'qa_decision_notes'):
                if field in request.POST:
                    setattr(record, field, request.POST.get(field, '').strip())
            if 'received_date' in request.POST:
                record.received_date = parse_date(request.POST.get('received_date') or '')
            if 'expiry_date' in request.POST:
                record.expiry_date = parse_date(request.POST.get('expiry_date') or '')
            if operation == 'submit_qa':
                if not record.result_summary.strip():
                    messages.error(request, 'Material QC results are required before QA review.')
                    return redirect('dashboards:qms_material_qc_detail', material_qc_id=record.id)
                record.status = 'qa_review'
            elif operation in {'approve', 'reject'}:
                if not is_qa or record.status != 'qa_review':
                    messages.error(request, 'Material QC must be in QA Review before disposition.')
                    return redirect('dashboards:qms_material_qc_detail', material_qc_id=record.id)
                record.approved_by = request.user
                record.approved_at = timezone.now()
                record.status = 'approved' if operation == 'approve' else 'rejected'
        elif record_type == 'supplier_quality':
            for field in ('supplier_name', 'supplier_code', 'material_name', 'risk_level', 'quality_agreement_reference', 'approval_notes'):
                if field in request.POST:
                    setattr(record, field, request.POST.get(field, '').strip())
            if 'next_audit_date' in request.POST:
                record.next_audit_date = parse_date(request.POST.get('next_audit_date') or '')
            if operation in {'approve', 'disqualify'}:
                if not is_qa:
                    messages.error(request, 'Only QA users can disposition supplier qualification.')
                    return redirect('dashboards:qms_supplier_quality_detail', supplier_id=record.id)
                record.approved_by = request.user
                record.status = 'approved' if operation == 'approve' else 'disqualified'
        record.save()
        activity_field = f'qc_{record_type}_workflow'
        activity_kwargs = {'action_type': 'approved' if operation in {'approve', 'verify'} else ('status_changed' if old_status != getattr(record, 'status', '') else 'updated'), 'field_changed': activity_field, 'old_value': old_status, 'new_value': getattr(record, 'status', ''), 'description': f'{record} {operation.replace("_", " ")}', 'user': request.user, 'ip_address': request.META.get('REMOTE_ADDR')}
        activity_kwargs['lab_investigation' if record_type == 'oos' else f'qms_{record_type}'] = record
        QMSActivityLog.objects.create(**activity_kwargs)
        messages.success(request, 'QC record updated.')
        return redirect(specs[record_type][1].replace('_id', '_detail') if False else {'oos': 'dashboards:qms_lab_investigation_detail', 'stability': 'dashboards:qms_stability_detail', 'coa': 'dashboards:qms_coa_detail', 'material_qc': 'dashboards:qms_material_qc_detail', 'supplier_quality': 'dashboards:qms_supplier_quality_detail'}[record_type], **{specs[record_type][1]: record.id})
    context = {'record_type': record_type, 'record_number': getattr(record, specs[record_type][2], str(record.pk)), 'record_title': str(record), 'record_status': record.get_status_display(), 'record_owner': getattr(getattr(record, 'owner', None), 'get_full_name', lambda: '')() or getattr(getattr(record, 'owner', None), 'username', ''), 'activity_log': getattr(record, 'activity_log').select_related('user').all()[:100], 'page_title': f'{record} - QC', 'users': get_user_model().objects.filter(is_active=True).order_by('username')}
    context[variable] = record
    if record_type == 'oos':
        context['bmr'] = record.bmr
    elif record_type == 'stability':
        context['results'] = record.results.select_related('analyst').all()
    elif record_type == 'material_qc':
        context['bmr'] = record.bmr
    return render(request, 'dashboards/qms/qc_record_detail.html', {**context, **_qms_relationship_context(record, {'oos': 'oos', 'stability': 'stability', 'coa': 'coa', 'material_qc': 'material_qc', 'supplier_quality': 'supplier_quality'}[record_type])})


@login_required
def qms_lab_investigation_detail(request, investigation_id):
    return _qms_qc_workspace(request, 'oos', investigation_id)


@login_required
def qms_stability_detail(request, stability_id):
    return _qms_qc_workspace(request, 'stability', stability_id)


@login_required
def qms_coa_detail(request, coa_id):
    return _qms_qc_workspace(request, 'coa', coa_id)


@login_required
def qms_material_qc_detail(request, material_qc_id):
    return _qms_qc_workspace(request, 'material_qc', material_qc_id)


@login_required
def qms_supplier_quality_detail(request, supplier_id):
    return _qms_qc_workspace(request, 'supplier_quality', supplier_id)


@login_required
def qms_training_detail(request, training_id):
    """Training assignment, completion, assessment, and effectiveness verification workspace."""
    training = get_object_or_404(QMSTrainingRecord.objects.select_related('document', 'trainee', 'trainer', 'verified_by'), pk=training_id)
    activity_log = training.activity_log.all().select_related('user')[:100]
    comments = training.comments.all().select_related('user')
    if request.method == 'POST':
        operation = request.POST.get('training_operation', 'save')
        role = getattr(request.user, 'role', None)
        is_qa = request.user.is_staff or role in {'qa', 'head_qa', 'admin'}
        if operation == 'verify' and not is_qa:
            messages.error(request, 'Only QA can verify training effectiveness.')
            return redirect('dashboards:qms_training_detail', training_id=training.id)
        old_status = training.status
        for field in ('training_type', 'delivery_method', 'objective', 'content_summary', 'completion_notes', 'assessment_result', 'effectiveness_result'):
            if field in request.POST:
                setattr(training, field, request.POST.get(field, '').strip())
        for field in ('assigned_date', 'due_date', 'completed_date', 'effectiveness_due_date'):
            if field in request.POST:
                setattr(training, field, parse_date(request.POST.get(field) or ''))
        if 'document' in request.POST:
            training.document_id = request.POST.get('document') or None
        if 'trainee' in request.POST:
            training.trainee_id = request.POST.get('trainee') or None
        if 'trainer' in request.POST:
            training.trainer_id = request.POST.get('trainer') or None
        if request.FILES.get('evidence_file'):
            training.evidence_file = request.FILES['evidence_file']
        if operation == 'start':
            training.status = 'in_progress'
        elif operation == 'complete':
            if not training.ready_for_completion:
                messages.error(request, 'Complete the training notes, assessment result, trainee, document, and completion date first.')
                return redirect('dashboards:qms_training_detail', training_id=training.id)
            training.status = 'awaiting_verification'
        elif operation == 'verify':
            if not training.effectiveness_result.strip():
                messages.error(request, 'Record the effectiveness result before verification.')
                return redirect('dashboards:qms_training_detail', training_id=training.id)
            training.verified_by = request.user
            training.verified_at = timezone.now()
            training.status = 'completed'
        elif operation == 'waive':
            training.status = 'waived'
        elif operation == 'reopen':
            training.status = 'in_progress'
        else:
            training.status = request.POST.get('status', training.status)
        training.save()
        QMSActivityLog.objects.create(qms_training=training, action_type='status_changed' if old_status != training.status else 'updated', field_changed='training_workflow', old_value=old_status, new_value=training.status, description=f'{training.training_number} {operation.replace("_", " ")}', user=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f'{training.training_number} updated.')
        return redirect('dashboards:qms_training_detail', training_id=training.id)
    return render(request, 'dashboards/qms/training_detail.html', {
        'training': training, 'users': get_user_model().objects.filter(is_active=True).order_by('username'),
        'documents': QMSDocument.objects.order_by('document_number')[:200], 'activity_log': activity_log, 'comments': comments,
        'page_title': f'{training.training_number} - Training', **_qms_relationship_context(training, 'training'),
    })


@login_required
def qms_regulatory_package_detail(request, package_id):
    """Regulatory package workspace: compile, QA review, submit, respond, approve, close."""
    package = get_object_or_404(
        QMSRegulatoryPackage.objects.select_related('owner', 'qa_reviewer', 'submitted_by', 'approved_by').prefetch_related('included_documents'),
        pk=package_id,
    )
    documents = QMSDocument.objects.order_by('document_number')[:200]
    activity_log = package.activity_log.all().select_related('user')[:100]
    attachments = package.attachments.all().select_related('uploaded_by')
    comments = package.comments.all().select_related('user')
    if request.method == 'POST':
        operation = request.POST.get('package_operation', 'save')
        role = getattr(request.user, 'role', None)
        is_qa = request.user.is_staff or role in {'qa', 'head_qa', 'admin'}
        is_regulatory = request.user.is_staff or role in {'regulatory', 'qa', 'head_qa', 'admin'}
        if operation in {'approve_internal', 'authority_approve', 'close'} and not is_regulatory:
            messages.error(request, 'Only Regulatory or QA users can approve or close a regulatory package.')
            return redirect('dashboards:qms_regulatory_package_detail', package_id=package.id)
        old_status = package.status
        for field in ('title', 'market', 'authority', 'dossier_reference', 'submission_type', 'scope_summary', 'dossier_summary', 'internal_qa_notes', 'authority_reference', 'authority_response', 'deficiencies', 'commitments', 'outcome_notes'):
            if field in request.POST:
                setattr(package, field, request.POST.get(field, '').strip())
        if 'owner' in request.POST:
            package.owner_id = request.POST.get('owner') or None
        if 'qa_reviewer' in request.POST:
            package.qa_reviewer_id = request.POST.get('qa_reviewer') or None
        if 'included_documents' in request.POST:
            package.included_documents.set(request.POST.getlist('included_documents'))
        for field in ('submission_date', 'approval_date', 'internal_approval_date', 'authority_response_date'):
            if field in request.POST:
                setattr(package, field, parse_date(request.POST.get(field) or ''))
        if operation == 'submit_qa':
            if not package.ready_for_qa_review:
                missing = []
                if not package.title.strip(): missing.append('title')
                if not package.market.strip(): missing.append('market')
                if not package.authority.strip(): missing.append('authority')
                if not package.owner_id: missing.append('package owner')
                if not package.scope_summary.strip(): missing.append('scope summary')
                if not package.dossier_summary.strip(): missing.append('dossier summary')
                if not package.included_documents.exists(): missing.append('at least one supporting document')
                messages.error(request, f'Complete the following before QA review: {", ".join(missing)}.')
                return redirect('dashboards:qms_regulatory_package_detail', package_id=package.id)
            package.status = 'qa_review'
        elif operation == 'approve_internal':
            if not package.ready_for_submission:
                messages.error(request, 'Assign a QA reviewer and complete internal QA notes and approval date before submission.')
                return redirect('dashboards:qms_regulatory_package_detail', package_id=package.id)
            package.approved_by = request.user
            package.internal_approval_date = package.internal_approval_date or timezone.now().date()
            package.status = 'submitted'
            package.submitted_by = request.user
            package.submission_date = package.submission_date or timezone.now().date()
            QMSElectronicSignature.objects.create(target_model='QMSRegulatoryPackage', target_object_id=package.id, meaning='Regulatory package internal approval', signer=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        elif operation == 'authority_approve':
            if package.status != 'submitted' or not package.authority_response.strip():
                messages.error(request, 'Record the authority response before approving the regulatory package.')
                return redirect('dashboards:qms_regulatory_package_detail', package_id=package.id)
            package.status = 'approved'
            package.approved_by = request.user
            package.approval_date = package.approval_date or timezone.now().date()
            package.authority_response_date = package.authority_response_date or timezone.now().date()
            QMSElectronicSignature.objects.create(target_model='QMSRegulatoryPackage', target_object_id=package.id, meaning='Regulatory authority outcome recorded', signer=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        elif operation == 'close':
            if not package.ready_for_close:
                messages.error(request, 'Record the approved outcome and closure notes before closing the package.')
                return redirect('dashboards:qms_regulatory_package_detail', package_id=package.id)
            package.status = 'closed'
            package.closed_at = timezone.now()
        elif operation == 'reject':
            package.status = 'rejected'
        elif operation == 'withdraw':
            package.status = 'withdrawn'
        else:
            package.status = request.POST.get('status', package.status)
        package.save()
        if old_status != package.status:
            QMSFieldAuditTrail.objects.create(model_name='QMSRegulatoryPackage', object_id=package.id, field_name='status', old_value=old_status, new_value=package.status, reason=f'Regulatory package workflow: {operation}', changed_by=request.user)
        QMSActivityLog.objects.create(qms_regulatory_package=package, action_type='status_changed' if old_status != package.status else 'updated', field_changed='regulatory_package_workflow', old_value=old_status, new_value=package.status, description=f'{package.package_number} {operation.replace("_", " ")}', user=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f'{package.package_number} updated.')
        return redirect('dashboards:qms_regulatory_package_detail', package_id=package.id)
    return render(request, 'dashboards/qms/regulatory_package_detail.html', {
        'package': package, 'documents': documents, 'users': get_user_model().objects.filter(is_active=True).order_by('username'),
        'activity_log': activity_log, 'attachments': attachments, 'comments': comments,
        'page_title': f'{package.package_number} - Regulatory Package',
        **_qms_relationship_context(package, 'regulatory'),
    })


@login_required
def qms_regulatory_packages(request):
    """Dedicated Regulatory Package register and entry point to package workspaces."""
    if getattr(request.user, 'role', None) not in {'regulatory', 'qa', 'head_qa', 'admin'} and not request.user.is_staff:
        messages.error(request, 'Access denied. Regulatory or QA role required.')
        return redirect('dashboards:dashboard_home')
    if request.method == 'POST':
        package = QMSRegulatoryPackage.objects.create(
            title=request.POST.get('title', '').strip(), market=request.POST.get('market', '').strip(),
            authority=request.POST.get('authority', '').strip(), submission_type=request.POST.get('submission_type', '').strip(),
            dossier_reference=request.POST.get('dossier_reference', '').strip(), owner_id=request.POST.get('owner') or request.user.id,
            status='draft', scope_summary=request.POST.get('scope_summary', '').strip(),
        )
        package.included_documents.set(request.POST.getlist('included_documents'))
        messages.success(request, f'{package.package_number} created. Complete the package in its workspace.')
        return redirect('dashboards:qms_regulatory_package_detail', package_id=package.id)
    status_filter = request.GET.get('status', '').strip()
    packages = QMSRegulatoryPackage.objects.select_related('owner', 'qa_reviewer', 'submitted_by', 'approved_by').prefetch_related('included_documents').order_by('-updated_at')
    if status_filter:
        packages = packages.filter(status=status_filter)
    return render(request, 'dashboards/qms/regulatory_packages.html', {
        'packages': packages, 'status_filter': status_filter,
        'status_choices': QMSRegulatoryPackage.STATUS_CHOICES,
        'documents': QMSDocument.objects.order_by('document_number')[:200],
        'users': get_user_model().objects.filter(is_active=True).order_by('username'),
        'page_title': 'Regulatory Packages',
    })


@login_required
def qms_quality_query_detail(request, query_id):
    """Full quality-query workflow from intake through QA-approved closure."""
    query = get_object_or_404(
        QMSQualityQuery.objects.select_related('assigned_to', 'created_by', 'responded_by', 'qa_approved_by', 'closed_by'),
        pk=query_id,
    )
    attachments = query.attachments.all().select_related('uploaded_by')
    comments = query.comments.all().select_related('user')
    activity_log = query.activity_log.all().select_related('user')[:100]
    if request.method == 'POST':
        operation = request.POST.get('query_operation', 'save')
        is_qa = request.user.is_staff or getattr(request.user, 'role', None) in {'qa', 'head_qa', 'admin'}
        if operation in {'approve', 'close'} and not is_qa:
            messages.error(request, 'Only QA reviewers can approve or close a quality query.')
            return redirect('dashboards:qms_quality_query_detail', query_id=query.id)
        old_status = query.status
        for field in ('query_type', 'priority', 'source', 'subject', 'question', 'response', 'impact_assessment',
                      'containment_action', 'investigation_notes', 'root_cause', 'qa_review_notes', 'resolution'):
            if field in request.POST:
                setattr(query, field, request.POST.get(field, '').strip())
        if 'assigned_to' in request.POST:
            query.assigned_to_id = request.POST.get('assigned_to') or None
        if 'due_date' in request.POST:
            query.due_date = parse_date(request.POST.get('due_date') or '')
        if operation == 'start_investigation':
            query.status = 'investigation'
        elif operation == 'submit_qa':
            if not query.ready_for_qa_review:
                messages.error(request, 'Assign an owner and complete the investigation and response before QA review.')
                return redirect('dashboards:qms_quality_query_detail', query_id=query.id)
            query.status = 'qa_review'
        elif operation == 'approve':
            if query.status != 'qa_review' or not query.ready_for_qa_review:
                messages.error(request, 'The query must be in QA review with a complete response before approval.')
                return redirect('dashboards:qms_quality_query_detail', query_id=query.id)
            query.qa_approved_by = request.user
            query.qa_approved_at = timezone.now()
            query.status = 'qa_approved'
            QMSElectronicSignature.objects.create(target_model='QMSQualityQuery', target_object_id=query.id, meaning='Quality query approval', signer=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        elif operation == 'close':
            if not query.ready_for_close:
                messages.error(request, 'QA approval, response owner, and resolution are required before closure.')
                return redirect('dashboards:qms_quality_query_detail', query_id=query.id)
            query.closed_by = request.user
            query.closed_at = timezone.now()
            query.status = 'closed'
        elif operation == 'reopen':
            query.status = 'investigation'
            query.closed_at = None
        else:
            query.status = request.POST.get('status', query.status)
        if query.status in {'responded', 'qa_review', 'qa_approved', 'closed'} and query.response and not query.responded_by_id:
            query.responded_by = request.user
            query.responded_at = timezone.now()
        query.save()
        if old_status != query.status:
            QMSFieldAuditTrail.objects.create(model_name='QMSQualityQuery', object_id=query.id, field_name='status', old_value=old_status, new_value=query.status, reason=f'Quality query workflow: {operation}', changed_by=request.user)
        QMSActivityLog.objects.create(qms_quality_query=query, action_type='status_changed' if old_status != query.status else 'updated', field_changed='query_workflow', old_value=old_status, new_value=query.status, description=f'{query.query_number} {operation.replace("_", " ")}', user=request.user, ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f'{query.query_number} updated.')
        return redirect('dashboards:qms_quality_query_detail', query_id=query.id)
    return render(request, 'dashboards/qms/quality_query_detail.html', {
        'query': query, 'attachments': attachments, 'comments': comments, 'activity_log': activity_log,
        'users': get_user_model().objects.filter(is_active=True).order_by('username'),
        'page_title': f'{query.query_number} - Quality Query',
        **_qms_relationship_context(query, 'query'),
    })


@login_required
@require_POST
def qms_quality_query_upload_file(request, query_id):
    query = get_object_or_404(QMSQualityQuery, pk=query_id)
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    attachment = QMSAttachment.objects.create(qms_quality_query=query, file=request.FILES['file'], description=request.POST.get('description', ''), uploaded_by=request.user)
    return JsonResponse({'success': True, 'attachment_id': attachment.id})


@login_required
@require_POST
def qms_quality_query_add_comment(request, query_id):
    query = get_object_or_404(QMSQualityQuery, pk=query_id)
    comment = QMSComment.objects.create(qms_quality_query=query, comment_text=request.POST.get('comment', '').strip(), user=request.user, is_internal=True)
    return JsonResponse({'success': True, 'comment_id': comment.id})


@login_required
@require_POST
def qms_regulatory_package_upload_file(request, package_id):
    package = get_object_or_404(QMSRegulatoryPackage, pk=package_id)
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    attachment = QMSAttachment.objects.create(qms_regulatory_package=package, file=request.FILES['file'], description=request.POST.get('description', ''), uploaded_by=request.user)
    return JsonResponse({'success': True, 'attachment_id': attachment.id})


@login_required
@require_POST
def qms_regulatory_package_add_comment(request, package_id):
    package = get_object_or_404(QMSRegulatoryPackage, pk=package_id)
    comment = QMSComment.objects.create(qms_regulatory_package=package, comment_text=request.POST.get('comment', '').strip(), user=request.user, is_internal=True)
    return JsonResponse({'success': True, 'comment_id': comment.id})


@login_required
@require_POST
def qms_document_upload_file(request, document_id):
    """Upload file to Document"""
    document = get_object_or_404(QMSDocument, pk=document_id)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    
    uploaded_file = request.FILES['file']
    description = request.POST.get('description', '')
    
    attachment = QMSAttachment.objects.create(
        qms_document=document,
        file=uploaded_file,
        description=description,
        uploaded_by=request.user
    )
    
    QMSActivityLog.objects.create(
        qms_document=document,
        action_type='file_uploaded',
        description=f'Uploaded file: {attachment.filename}',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'uploaded_by': attachment.uploaded_by.username,
            'uploaded_at': attachment.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
@require_POST
def qms_document_add_comment(request, document_id):
    """Add comment to Document"""
    document = get_object_or_404(QMSDocument, pk=document_id)
    
    comment_text = request.POST.get('comment', '').strip()
    if not comment_text:
        return JsonResponse({'success': False, 'error': 'Comment cannot be empty'}, status=400)
    
    is_internal = request.POST.get('is_internal') == '1'
    
    comment = QMSComment.objects.create(
        qms_document=document,
        comment_text=comment_text,
        user=request.user,
        is_internal=is_internal
    )
    
    QMSActivityLog.objects.create(
        qms_document=document,
        action_type='comment_added',
        description=f'Added comment',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'comment_text': comment.comment_text,
            'user': comment.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_internal': comment.is_internal,
        }
    })


# ============================================================================
# QMS DEVIATION DETAIL VIEW
# ============================================================================

@login_required
def qms_deviation_detail(request, deviation_id):
    """View full Deviation with attachments, comments, and activity log"""
    from .models import QMSDeviation
    deviation = get_object_or_404(QMSDeviation.objects.select_related('qms_action__created_by'), pk=deviation_id)
    
    attachments = deviation.attachments.all().select_related('uploaded_by')
    comments = deviation.comments.all().select_related('user')
    activity_log = deviation.activity_log.all().select_related('user')[:50]
    
    if request.method == 'POST':
        if 'update_status' in request.POST:
            old_status = deviation.status
            new_status = request.POST.get('status')
            
            if new_status and new_status != old_status:
                deviation.status = new_status
                deviation.save()
                
                QMSActivityLog.objects.create(
                    qms_deviation=deviation,
                    action_type='status_changed',
                    field_changed='status',
                    old_value=old_status,
                    new_value=new_status,
                    description=f'Status changed from {old_status} to {new_status}',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Status updated to {deviation.get_status_display()}')
            
            return redirect('dashboards:qms_deviation_detail', deviation_id=deviation.id)
    
    context = {
        'deviation': deviation,
        'attachments': attachments,
        'comments': comments,
        'activity_log': activity_log,
        'page_title': f'{deviation.deviation_number} - {deviation.title}',
        **_qms_relationship_context(deviation, 'deviation'),
    }
    
    return render(request, 'dashboards/qms/deviation_detail.html', context)


@login_required
@require_POST
def qms_deviation_upload_file(request, deviation_id):
    """Upload file to Deviation"""
    from .models import QMSDeviation
    deviation = get_object_or_404(QMSDeviation, pk=deviation_id)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    
    uploaded_file = request.FILES['file']
    description = request.POST.get('description', '')
    
    attachment = QMSAttachment.objects.create(
        qms_deviation=deviation,
        file=uploaded_file,
        description=description,
        uploaded_by=request.user
    )
    
    QMSActivityLog.objects.create(
        qms_deviation=deviation,
        action_type='file_uploaded',
        description=f'Uploaded file: {attachment.filename}',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'uploaded_by': attachment.uploaded_by.username,
            'uploaded_at': attachment.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
@require_POST
def qms_deviation_add_comment(request, deviation_id):
    """Add comment to Deviation"""
    from .models import QMSDeviation
    deviation = get_object_or_404(QMSDeviation, pk=deviation_id)
    
    comment_text = request.POST.get('comment', '').strip()
    if not comment_text:
        return JsonResponse({'success': False, 'error': 'Comment cannot be empty'}, status=400)
    
    is_internal = request.POST.get('is_internal') == '1'
    
    comment = QMSComment.objects.create(
        qms_deviation=deviation,
        comment_text=comment_text,
        user=request.user,
        is_internal=is_internal
    )
    
    QMSActivityLog.objects.create(
        qms_deviation=deviation,
        action_type='comment_added',
        description=f'Added comment',
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'comment_text': comment.comment_text,
            'user': comment.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_internal': comment.is_internal,
        }
    })


# ============================================================================
# QMS ATTACHMENT DOWNLOAD & DELETE
# ============================================================================

@login_required
def qms_attachment_download(request, attachment_id):
    """Download QMS attachment file"""
    attachment = get_object_or_404(QMSAttachment, pk=attachment_id)
    
    # Check if file exists
    if not attachment.file:
        messages.error(request, 'File not found')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Return file response
    response = FileResponse(attachment.file.open('rb'), as_attachment=True, filename=attachment.filename)
    
    # Set content type
    content_type, _ = mimetypes.guess_type(attachment.filename)
    if content_type:
        response['Content-Type'] = content_type
    
    return response


@login_required
@require_POST
def qms_attachment_delete(request, attachment_id):
    """Delete QMS attachment"""
    attachment = get_object_or_404(QMSAttachment, pk=attachment_id)
    
    # Log deletion before deleting
    record_type = None
    record_id = None
    if attachment.qms_action:
        record_type = 'qms_action'
        record_id = attachment.qms_action.id
        QMSActivityLog.objects.create(
            qms_action=attachment.qms_action,
            action_type='deleted',
            description=f'Deleted file: {attachment.filename}',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    elif attachment.qms_audit:
        record_type = 'qms_audit'
        record_id = attachment.qms_audit.id
        QMSActivityLog.objects.create(
            qms_audit=attachment.qms_audit,
            action_type='deleted',
            description=f'Deleted file: {attachment.filename}',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    elif attachment.qms_risk:
        record_type = 'qms_risk'
        record_id = attachment.qms_risk.id
        QMSActivityLog.objects.create(
            qms_risk=attachment.qms_risk,
            action_type='deleted',
            description=f'Deleted file: {attachment.filename}',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    elif attachment.qms_document:
        record_type = 'qms_document'
        record_id = attachment.qms_document.id
        QMSActivityLog.objects.create(
            qms_document=attachment.qms_document,
            action_type='deleted',
            description=f'Deleted file: {attachment.filename}',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    elif attachment.qms_deviation:
        record_type = 'qms_deviation'
        record_id = attachment.qms_deviation.id
        QMSActivityLog.objects.create(
            qms_deviation=attachment.qms_deviation,
            action_type='deleted',
            description=f'Deleted file: {attachment.filename}',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    
    # Delete file
    attachment.delete()
    
    messages.success(request, f'File "{attachment.filename}" deleted successfully')
    
    # Return JSON response for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    # Redirect back to detail page
    if record_type == 'qms_action':
        return redirect('dashboards:qms_action_detail', action_id=record_id)
    elif record_type == 'qms_audit':
        return redirect('dashboards:qms_audit_detail', audit_id=record_id)
    elif record_type == 'qms_risk':
        return redirect('dashboards:qms_risk_detail', risk_id=record_id)
    elif record_type == 'qms_document':
        return redirect('dashboards:qms_document_detail', document_id=record_id)
    elif record_type == 'qms_deviation':
        return redirect('dashboards:qms_deviation_detail', deviation_id=record_id)
    else:
        return redirect('dashboards:head_qa_dashboard')
