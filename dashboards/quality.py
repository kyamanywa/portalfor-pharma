from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import (
    QMSAction,
    QualityDefect,
    QualityInspectionCharacteristic,
    QualityInspectionLot,
    QualityResult,
)


QC_PHASE_NAMES = {
    'post_compression_qc',
    'post_mixing_qc',
    'post_blending_qc',
}

QUALITY_TEMPLATE_PHASE_ALIASES = {
    'post_blending_qc': ['post_blending_qc', 'blending'],
    'post_mixing_qc': ['post_mixing_qc', 'mixing'],
    'post_compression_qc': ['post_compression_qc', 'compression'],
}

SAP_STYLE_DEFAULT_CHARACTERISTICS = {
    'tablet': [
        ('Appearance', 'Visual inspection', 'Conforms to approved product description', None, None, ''),
        ('Average weight', 'In-process weight check', 'Within approved product limits', None, None, 'mg'),
        ('Hardness', 'Hardness tester', 'Within approved product limits', None, None, 'kg/cm2'),
        ('Friability', 'Friability test', 'NMT approved limit', None, None, '%'),
        ('Disintegration', 'Disintegration test', 'NMT approved limit', None, None, 'min'),
        ('Assay', 'Approved assay method', 'Within approved assay range', None, None, '%'),
    ],
    'capsule': [
        ('Appearance', 'Visual inspection', 'Conforms to approved product description', None, None, ''),
        ('Fill weight', 'Weight variation', 'Within approved product limits', None, None, 'mg'),
        ('Disintegration', 'Disintegration test', 'NMT approved limit', None, None, 'min'),
        ('Assay', 'Approved assay method', 'Within approved assay range', None, None, '%'),
    ],
    'ointment': [
        ('Appearance', 'Visual inspection', 'Conforms to approved product description', None, None, ''),
        ('Homogeneity', 'Approved homogeneity method', 'Uniform preparation', None, None, ''),
        ('Net content', 'Weight/content check', 'Within approved product limits', None, None, 'g'),
        ('Assay', 'Approved assay method', 'Within approved assay range', None, None, '%'),
    ],
}


def _inspection_type_for_phase(phase_name):
    if phase_name == 'final_qa':
        return 'final'
    if phase_name in QC_PHASE_NAMES:
        return 'in_process'
    return 'manual'


def _product_family(product):
    product_type = getattr(product, 'product_type', '') or ''
    if product_type.startswith('tablet'):
        return 'tablet'
    if product_type.startswith('capsule'):
        return 'capsule'
    if product_type.startswith('ointment'):
        return 'ointment'
    return product_type or 'tablet'


def ensure_inspection_lot_for_phase(phase_execution, created_by=None):
    """
    Create or return the SAP-QM-style inspection lot that shadows a workflow
    phase. This does not change workflow progression; it adds quality records
    beside the existing BMR phase execution.
    """
    if not phase_execution:
        return None

    phase_name = phase_execution.phase.phase_name
    defaults = {
        'bmr': phase_execution.bmr,
        'product': phase_execution.bmr.product,
        'inspection_type': _inspection_type_for_phase(phase_name),
        'origin': 'workflow_phase',
        'created_by': created_by,
        'assigned_to': created_by if getattr(created_by, 'role', None) in ('qa', 'qc') else None,
    }

    with transaction.atomic():
        lot, created = QualityInspectionLot.objects.get_or_create(
            phase_execution=phase_execution,
            defaults=defaults,
        )
        if created:
            seed_characteristics(lot)
        else:
            ensure_template_characteristics(lot)
        return lot


def seed_characteristics(lot):
    template_rows = _template_characteristics_for_lot(lot)
    if template_rows:
        QualityInspectionCharacteristic.objects.bulk_create(template_rows)
        return

    product = lot.product
    family = _product_family(product)
    defaults = SAP_STYLE_DEFAULT_CHARACTERISTICS.get(family, SAP_STYLE_DEFAULT_CHARACTERISTICS['tablet'])

    rows = []
    for order, (name, method, spec, lower, upper, unit) in enumerate(defaults, start=1):
        rows.append(QualityInspectionCharacteristic(
            lot=lot,
            name=name,
            test_method=method,
            specification=spec,
            lower_limit=lower,
            upper_limit=upper,
            unit=unit,
            order=order,
        ))
    QualityInspectionCharacteristic.objects.bulk_create(rows)


def ensure_template_characteristics(lot):
    """Add template-derived characteristics to an existing lot if missing."""
    if lot.characteristics.filter(template_section__isnull=False).exists():
        _ensure_characteristic_template_fields(lot)
        return
    template_rows = _template_characteristics_for_lot(lot)
    if template_rows:
        QualityInspectionCharacteristic.objects.bulk_create(template_rows)


def _template_characteristics_for_lot(lot):
    """Build QC characteristics from BMR template sections/fields where possible."""
    if not lot.phase_execution:
        return []

    phase_name = lot.phase_execution.phase.phase_name
    product = lot.product
    try:
        from bmr.models import BMRTemplate
        from bmr.template_models import BMRTemplateField, BMRTemplateSection
    except Exception:
        return []

    template = BMRTemplate.for_product(product)
    if not template:
        return []

    phase_names = QUALITY_TEMPLATE_PHASE_ALIASES.get(phase_name, [phase_name])
    quality_section_types = ['qa_report', 'form'] if phase_name in QC_PHASE_NAMES else ['qa_report', 'ipc_table', 'form']
    sections = (
        BMRTemplateSection.objects
        .filter(
            template=template,
            phase_name__in=phase_names,
            section_type__in=quality_section_types,
            is_visible=True,
        )
        .prefetch_related('fields')
        .order_by('page_number', 'order')
    )

    rows = []
    order = 1
    for section in sections:
        fields = list(section.fields.order_by('order'))
        measurable_fields = [
            field for field in fields
            if field.field_type in ('number', 'decimal', 'text', 'textarea', 'select', 'radio')
            and not field.is_readonly
        ]
        if not measurable_fields:
            config_rows = _config_characteristics(section, BMRTemplateField, order)
            if config_rows:
                for field, label, spec in config_rows:
                    rows.append(QualityInspectionCharacteristic(
                        lot=lot,
                        template_section=section,
                        template_field=field,
                        name=f'{section.title} - {label}',
                        test_method=section.get_section_type_display(),
                        specification=spec,
                        order=order,
                    ))
                    order += 1
            else:
                rows.append(QualityInspectionCharacteristic(
                    lot=lot,
                    template_section=section,
                    name=section.title,
                    test_method=section.description or section.get_section_type_display(),
                    specification=section.config.get('specification', 'Complete per approved BMR template section'),
                    order=order,
                ))
                order += 1
            continue

        for field in measurable_fields:
            spec_parts = []
            if field.min_value is not None:
                spec_parts.append(f'Min {field.min_value}')
            if field.max_value is not None:
                spec_parts.append(f'Max {field.max_value}')
            if field.help_text:
                spec_parts.append(field.help_text)
            rows.append(QualityInspectionCharacteristic(
                lot=lot,
                template_section=section,
                template_field=field,
                name=f'{section.title} - {field.label}',
                test_method=section.get_section_type_display(),
                specification='; '.join(spec_parts) or field.placeholder or 'Record result per approved BMR template',
                lower_limit=field.min_value,
                upper_limit=field.max_value,
                order=order,
            ))
            order += 1

    return rows


def _config_characteristics(section, field_model, start_order):
    """
    Convert section config tests/fields into persistent template fields so QC
    results can write back through the same BMRFormData mechanism.
    """
    config = section.config or {}
    candidates = []

    for item in config.get('tests') or []:
        label = item.get('test') or item.get('label') or item.get('name')
        if label:
            candidates.append((label, item.get('spec') or item.get('specification') or 'Record result per approved BMR template'))

    for item in config.get('fields') or []:
        label = item.get('label') or item.get('key') or item.get('name')
        if label:
            candidates.append((label, item.get('spec') or item.get('help_text') or 'Record value per approved BMR template'))

    if section.section_type == 'ipc_table':
        for item in config.get('columns') or config.get('header_fields') or []:
            label = item.get('label') or item.get('header') or item.get('key') or item.get('name')
            if label:
                candidates.append((label, item.get('spec') or item.get('help_text') or config.get('fill_weight_spec') or 'Record IPC result per approved BMR template'))
        if not candidates and config.get('fill_weight_spec'):
            candidates.append(('Fill weight / IPC result', config.get('fill_weight_spec')))

    rows = []
    for offset, (label, spec) in enumerate(candidates, start=start_order):
        field = _get_or_create_quality_template_field(field_model, section, label, spec, offset)
        rows.append((field, label, spec))
    return rows


def _get_or_create_quality_template_field(field_model, section, label, spec, order):
    field = field_model.objects.filter(section=section, label=label).first()
    if field:
        return field
    return field_model.objects.create(
        section=section,
        label=label,
        field_type='text',
        data_source='manual',
        order=order,
        is_required=True,
        help_text=spec,
        placeholder=spec[:200],
    )


def _ensure_characteristic_template_fields(lot):
    missing = lot.characteristics.filter(template_section__isnull=False, template_field__isnull=True)
    if not missing.exists():
        return
    try:
        from bmr.template_models import BMRTemplateField
    except Exception:
        return

    for characteristic in missing.select_related('template_section'):
        section = characteristic.template_section
        field = _get_or_create_quality_template_field(
            BMRTemplateField,
            section,
            characteristic.name.replace(f'{section.title} - ', ''),
            characteristic.specification,
            characteristic.order,
        )
        characteristic.template_field = field
        characteristic.save(update_fields=['template_field'])


def mark_lot_started(phase_execution, user, notes=''):
    lot = ensure_inspection_lot_for_phase(phase_execution, user)
    if not lot:
        return None
    if lot.status in ('created', 'released'):
        lot.status = 'in_inspection'
        lot.assigned_to = user
        lot.started_at = lot.started_at or timezone.now()
        lot.decision_notes = notes or lot.decision_notes
        lot.save(update_fields=['status', 'assigned_to', 'started_at', 'decision_notes', 'updated_at'])
    return lot


def record_usage_decision(phase_execution, decision, user, notes=''):
    lot = ensure_inspection_lot_for_phase(phase_execution, user)
    if not lot:
        return None

    lot.status = 'accepted' if decision == 'accept' else 'rejected'
    lot.usage_decision = 'unrestricted' if decision == 'accept' else 'rework'
    lot.decision_by = user
    lot.decision_at = timezone.now()
    lot.completed_at = lot.decision_at
    lot.decision_notes = notes
    lot.save()

    if decision != 'accept':
        defect = QualityDefect.objects.create(
            lot=lot,
            defect_type='out_of_specification',
            severity='major',
            description=notes or 'Quality inspection failed and requires rework.',
            reported_by=user,
        )
        ensure_qms_actions_for_defect(defect, user)

    return lot


def sync_completed_phase_lot(phase_execution):
    """
    Backfill/synchronize a completed or failed QC phase into an inspection lot.
    This lets older QC executions appear in the Quality Lots UI without changing
    workflow status or rollback behavior.
    """
    lot = ensure_inspection_lot_for_phase(
        phase_execution,
        getattr(phase_execution, 'completed_by', None) or getattr(phase_execution, 'started_by', None),
    )
    if not lot or lot.status in ('accepted', 'rejected', 'cancelled'):
        return lot

    if phase_execution.status == 'completed':
        lot.status = 'accepted'
        lot.usage_decision = 'unrestricted'
    elif phase_execution.status == 'failed':
        lot.status = 'rejected'
        lot.usage_decision = 'rework'
    else:
        return lot

    lot.decision_by = phase_execution.completed_by
    lot.decision_at = phase_execution.completed_date or timezone.now()
    lot.completed_at = phase_execution.completed_date or lot.decision_at
    lot.decision_notes = phase_execution.operator_comments or lot.decision_notes
    lot.save()

    if phase_execution.status == 'failed' and not lot.defects.exists():
        defect = QualityDefect.objects.create(
            lot=lot,
            defect_type='out_of_specification',
            severity='major',
            description=phase_execution.operator_comments or 'Historical QC failure synced from workflow phase.',
            reported_by=phase_execution.completed_by,
        )
        ensure_qms_actions_for_defect(defect, phase_execution.completed_by)

    return lot


def ensure_qms_actions_for_defect(defect, user=None):
    """Create role-routed QMS work items for an OOS/deviation defect."""
    lot = defect.lot
    base_defaults = {
        'bmr': lot.bmr,
        'product': lot.product,
        'quality_lot': lot,
        'defect': defect,
        'created_by': user,
        'priority': 'critical' if defect.severity == 'critical' else 'high',
        'due_date': timezone.localdate() + timedelta(days=7),
    }

    QMSAction.objects.get_or_create(
        defect=defect,
        category='deviation',
        owner_role='qa',
        defaults={
            **base_defaults,
            'title': f'Deviation/OOS investigation for {lot.lot_number}',
            'description': defect.description,
            'status': 'investigation',
        },
    )
    QMSAction.objects.get_or_create(
        defect=defect,
        category='capa',
        owner_role='qa',
        defaults={
            **base_defaults,
            'title': f'CAPA required for {lot.bmr.batch_number}',
            'description': 'Define corrective and preventive actions before batch disposition.',
            'status': 'action_required',
            'due_date': timezone.localdate() + timedelta(days=14),
        },
    )
    QMSAction.objects.get_or_create(
        defect=defect,
        category='deviation',
        owner_role='qc',
        defaults={
            **base_defaults,
            'title': f'QC OOS lab investigation for {lot.lot_number}',
            'description': 'Review analytical result, method, sample handling, and repeat/confirmatory testing where approved.',
            'status': 'investigation',
        },
    )


def sync_lots_for_dashboard(phases, user=None):
    lots = []
    for phase_execution in phases:
        lot = ensure_inspection_lot_for_phase(phase_execution, user)
        if lot:
            lots.append(lot)
    return lots


def save_characteristic_results(lot, post_data, user):
    """Persist result rows for a lot detail form."""
    for characteristic in lot.characteristics.all():
        value_text = post_data.get(f'value_text_{characteristic.pk}', '').strip()
        numeric_raw = post_data.get(f'numeric_value_{characteristic.pk}', '').strip()
        passed_raw = post_data.get(f'passed_{characteristic.pk}', '')
        comments = post_data.get(f'comments_{characteristic.pk}', '').strip()

        numeric_value = None
        if numeric_raw:
            try:
                numeric_value = numeric_raw
            except Exception:
                numeric_value = None

        passed = None
        if passed_raw == 'pass':
            passed = True
        elif passed_raw == 'fail':
            passed = False

        if value_text or numeric_raw or passed is not None or comments:
            result = QualityResult.objects.create(
                characteristic=characteristic,
                value_text=value_text,
                numeric_value=numeric_value,
                passed=passed,
                comments=comments,
                recorded_by=user,
            )
            sync_result_to_bmr_template(characteristic, result, user)

    if lot.status in ('created', 'released'):
        lot.status = 'results_recorded'
        lot.save(update_fields=['status', 'updated_at'])


def sync_result_to_bmr_template(characteristic, result, user):
    """
    Mirror QC results into the BMR template data store when the characteristic
    was derived from a BMR template field.
    """
    section = characteristic.template_section
    field = characteristic.template_field
    lot = characteristic.lot
    if not section or not field or not lot.bmr:
        return

    value = _template_value_from_result(result)
    if value == '':
        return

    try:
        from bmr.template_models import BMRFormData
    except Exception:
        return

    BMRFormData.objects.update_or_create(
        bmr=lot.bmr,
        section=section,
        field=field,
        defaults={
            'value': value,
            'created_by': user,
        },
    )
    _sync_result_to_phase_data(characteristic, value, result, user)


def _template_value_from_result(result):
    if result.numeric_value is not None:
        return str(result.numeric_value)
    if result.value_text:
        return result.value_text
    if result.passed is True:
        return 'Pass'
    if result.passed is False:
        return 'Fail'
    return ''


def _sync_result_to_phase_data(characteristic, value, result, user):
    lot = characteristic.lot
    phase_execution = lot.phase_execution
    section = characteristic.template_section
    field = characteristic.template_field
    if not phase_execution or not section or not field:
        return

    phase_name = phase_execution.phase.phase_name
    phase_data = phase_execution.phase_data or {}
    phase_block = phase_data.setdefault(phase_name, {})
    section_block = phase_block.setdefault(str(section.pk), {})
    section_block[f'f_{field.pk}'] = value
    section_block[f'_qc_result_{field.pk}'] = {
        'lot_number': lot.lot_number,
        'result_id': result.pk,
        'passed': result.passed,
        'comments': result.comments,
        'recorded_by': user.get_full_name() or user.username,
        'recorded_at': timezone.now().isoformat(),
    }
    phase_block['_last_saved_by'] = user.get_full_name() or user.username
    phase_block['_last_saved_at'] = timezone.now().isoformat()
    phase_execution.phase_data = phase_data
    phase_execution.save(update_fields=['phase_data'])
