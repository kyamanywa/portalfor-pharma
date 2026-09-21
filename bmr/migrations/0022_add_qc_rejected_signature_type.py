from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmr', '0021_bmrsignature_reauthentication'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bmrsignature',
            name='signature_type',
            field=models.CharField(
                choices=[
                    ('created', 'Created'),
                    ('reviewed', 'Reviewed'),
                    ('approved', 'Approved'),
                    ('dispensed', 'Materials Dispensed'),
                    ('production_started', 'Production Started'),
                    ('production_completed', 'Production Completed'),
                    ('qc_approved', 'QC Approved'),
                    ('qc_rejected', 'QC Rejected'),
                    ('final_approval', 'Final Approval'),
                ],
                max_length=30,
            ),
        ),
    ]
