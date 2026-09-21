from django.db import migrations


def backfill_capa_records(apps, schema_editor):
    from django.utils import timezone

    QMSAction = apps.get_model('dashboards', 'QMSAction')
    QMSCAPA = apps.get_model('dashboards', 'QMSCAPA')
    status_map = {
        'open': 'initiated',
        'investigation': 'investigation',
        'action_required': 'action_plan',
        'pending_approval': 'effectiveness_review',
        'closed': 'closed',
        'cancelled': 'cancelled',
    }
    prefix = f'CAPA{timezone.now().year}'
    next_number = 1
    for action in QMSAction.objects.filter(category='capa').order_by('pk').iterator():
        if QMSCAPA.objects.filter(qms_action_id=action.pk).exists():
            continue
        QMSCAPA.objects.create(
            capa_number=f'{prefix}{next_number:05d}',
            qms_action_id=action.pk,
            source_type='other',
            problem_statement=action.description,
            root_cause_analysis=action.root_cause,
            corrective_action_plan=action.corrective_action,
            preventive_action_plan=action.preventive_action,
            effectiveness_evidence=action.effectiveness_check,
            action_owner_id=action.assigned_to_id,
            target_completion_date=action.due_date,
            status=status_map.get(action.status, 'initiated'),
            priority=action.priority,
            created_by_id=action.created_by_id,
            approved_by_id=action.approved_by_id,
            closed_at=action.closed_at,
        )
        next_number += 1


class Migration(migrations.Migration):
    dependencies = [('dashboards', '0020_qmscapa')]

    operations = [migrations.RunPython(backfill_capa_records, migrations.RunPython.noop)]
