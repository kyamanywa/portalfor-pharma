from django.db import migrations


def backfill_change_controls(apps, schema_editor):
    from django.utils import timezone

    QMSAction = apps.get_model('dashboards', 'QMSAction')
    QMSChangeControl = apps.get_model('dashboards', 'QMSChangeControl')
    QMSChangeImpactAssessment = apps.get_model('dashboards', 'QMSChangeImpactAssessment')
    status_map = {
        'open': 'initiated',
        'investigation': 'impact_assessment',
        'action_required': 'implementation',
        'pending_approval': 'qa_review',
        'closed': 'closed',
        'cancelled': 'cancelled',
    }
    prefix = f'CC{timezone.now().year}'
    next_number = 1
    for action in QMSAction.objects.filter(category='change_control').order_by('pk').iterator():
        if QMSChangeControl.objects.filter(qms_action_id=action.pk).exists():
            continue
        impact = QMSChangeImpactAssessment.objects.filter(change_action_id=action.pk).order_by('-assessed_at').first()
        QMSChangeControl.objects.create(
            change_number=f'{prefix}{next_number:05d}',
            qms_action_id=action.pk,
            risk_level=action.priority,
            justification=action.description,
            current_state='Existing process or system state not recorded in the legacy action.',
            proposed_state=action.description,
            quality_impact=getattr(impact, 'bmr_impact', False) if impact else False,
            gmp_impact=getattr(impact, 'regulatory_impact', False) if impact else False,
            validation_impact=getattr(impact, 'validation_impact', False) if impact else False,
            regulatory_impact=getattr(impact, 'regulatory_impact', False) if impact else False,
            training_impact=getattr(impact, 'training_impact', False) if impact else False,
            stability_impact=getattr(impact, 'stability_impact', False) if impact else False,
            inventory_impact=getattr(impact, 'inventory_impact', False) if impact else False,
            impact_summary=getattr(impact, 'impact_summary', '') if impact else '',
            qa_impact_decision=getattr(impact, 'qa_decision', '') if impact else '',
            implementation_notes=action.description if action.status == 'closed' else '',
            owner_id=action.assigned_to_id,
            implementation_owner_id=action.assigned_to_id,
            planned_implementation_date=action.due_date,
            actual_implementation_date=action.closed_at.date() if action.closed_at else None,
            status=status_map.get(action.status, 'initiated'),
            created_by_id=action.created_by_id,
            approved_by_id=action.approved_by_id,
            approved_at=action.closed_at if action.status == 'closed' else None,
            closed_by_id=action.approved_by_id,
            closed_at=action.closed_at,
        )
        next_number += 1


class Migration(migrations.Migration):
    dependencies = [('dashboards', '0023_qmschangecontrol')]

    operations = [migrations.RunPython(backfill_change_controls, migrations.RunPython.noop)]
