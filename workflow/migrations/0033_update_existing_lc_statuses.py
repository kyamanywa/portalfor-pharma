"""
Data migration: Set beginning_lc_status and ending_lc_status correctly for existing records.
- Phases WITH line clearance: 'not_started' (default was already 'not_started', so no change)
- Phases WITHOUT line clearance: 'not_required' (was 'not_started', now corrected)
"""
from django.db import migrations

# Phases that have line clearance (from line_clearance_items.py)
PHASES_WITH_LC = [
    'dispensing', 'material_dispensing', 'granulation', 'blending',
    'compression', 'sorting', 'blister_packing', 'bulk_packing',
    'secondary_packaging',
]


def update_lc_statuses(apps, schema_editor):
    BatchPhaseExecution = apps.get_model('workflow', 'BatchPhaseExecution')
    
    # Set all phases currently 'not_started' to 'not_required' UNLESS they have LC
    updated = BatchPhaseExecution.objects.filter(
        beginning_lc_status='not_started',
    ).exclude(
        phase__phase_name__in=PHASES_WITH_LC,
    ).update(
        beginning_lc_status='not_required',
        ending_lc_status='not_required',
    )
    print(f"  Updated {updated} phase executions without LC to 'not_required'")


def reverse_lc_statuses(apps, schema_editor):
    BatchPhaseExecution = apps.get_model('workflow', 'BatchPhaseExecution')
    BatchPhaseExecution.objects.filter(
        beginning_lc_status='not_required',
    ).update(
        beginning_lc_status='not_started',
        ending_lc_status='not_started',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0032_change_lc_status_default_to_not_required'),
    ]

    operations = [
        migrations.RunPython(update_lc_statuses, reverse_lc_statuses),
    ]
