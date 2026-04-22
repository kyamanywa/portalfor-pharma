from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmr', '0010_bmrtemplatesection_bmrtemplatefield_bmrtemplatetable_and_more'),
    ]

    operations = [
        # Add product_type to BMRTemplate
        migrations.AddField(
            model_name='bmrtemplate',
            name='product_type',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                max_length=20,
                choices=[
                    ('', 'Universal (all types)'),
                    ('tablet_normal', 'Tablet Normal'),
                    ('tablet_type_2', 'Tablet Type 2'),
                    ('ointment', 'Ointment'),
                    ('capsule', 'Capsule'),
                ],
                help_text='The product type this template applies to. Leave blank for a universal template.',
            ),
        ),
        # Add phase_name to BMRTemplateSection
        migrations.AddField(
            model_name='bmrtemplatesection',
            name='phase_name',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                max_length=50,
                help_text='Workflow phase this section belongs to (e.g. mixing, tube_filling, blister_packing)',
            ),
        ),
        # Add config JSONField to BMRTemplateSection
        migrations.AddField(
            model_name='bmrtemplatesection',
            name='config',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Section-specific config: step instructions, IPC row count, etc.',
            ),
        ),
        # Alter section_type to include new dynamic types (wider max_length)
        migrations.AlterField(
            model_name='bmrtemplatesection',
            name='section_type',
            field=models.CharField(
                default='info',
                max_length=25,
                choices=[
                    ('info', 'Information Section'),
                    ('form', 'Form Section'),
                    ('table', 'Table Section'),
                    ('signature', 'Signature Section'),
                    ('divider', 'Page Break/Divider'),
                    ('line_clearance', 'Line Clearance'),
                    ('process_steps', 'Process Steps'),
                    ('qa_report', 'QA Report'),
                    ('yield_reconciliation', 'Yield Reconciliation'),
                    ('ipc_table', 'IPC Table (In-Process Control)'),
                    ('coding_control', 'Coding Control / Secondary IPC'),
                    ('equipment_setup', 'Equipment Setup'),
                ],
            ),
        ),
    ]
