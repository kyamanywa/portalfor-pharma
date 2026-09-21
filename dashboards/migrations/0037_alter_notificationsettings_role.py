from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0036_qmsactivitylog_qms_stability_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationsettings',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('qa', 'QA'),
                    ('qc', 'QC'),
                    ('regulatory', 'Regulatory'),
                    ('production_manager', 'Production Manager'),
                    ('store_manager', 'Store Manager'),
                    ('mixing_operator', 'Mixing Operator'),
                    ('granulation_operator', 'Granulation Operator'),
                    ('blending_operator', 'Blending Operator'),
                    ('compression_operator', 'Compression Operator'),
                    ('coating_operator', 'Coating Operator'),
                    ('filling_operator', 'Filling Operator'),
                    ('tube_filling_operator', 'Tube Filling Operator'),
                    ('packing_operator', 'Packing Operator'),
                    ('sorting_operator', 'Sorting Operator'),
                    ('dispensing_operator', 'Dispensing Operator'),
                    ('maintenance', 'Maintenance Technician'),
                    ('equipment_operator', 'Equipment Operator'),
                ],
                max_length=50,
                unique=True,
            ),
        ),
    ]
