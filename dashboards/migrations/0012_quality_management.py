from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bmr', '0019_historicalbmr'),
        ('dashboards', '0011_alter_notificationsettings_role'),
        ('products', '0035_product_capsule_type'),
        ('workflow', '0035_alter_productionphase_phase_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='QualityInspectionLot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lot_number', models.CharField(blank=True, max_length=30, unique=True)),
                ('inspection_type', models.CharField(choices=[('in_process', 'In-Process Inspection'), ('final', 'Final Inspection'), ('quarantine', 'Quarantine Sample'), ('material', 'Material Inspection'), ('manual', 'Manual Inspection')], max_length=20)),
                ('origin', models.CharField(choices=[('workflow_phase', 'Workflow Phase'), ('quarantine', 'Quarantine'), ('manual', 'Manual')], default='workflow_phase', max_length=20)),
                ('status', models.CharField(choices=[('created', 'Created'), ('released', 'Released'), ('in_inspection', 'In Inspection'), ('results_recorded', 'Results Recorded'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='created', max_length=20)),
                ('usage_decision', models.CharField(blank=True, choices=[('', 'No Decision'), ('unrestricted', 'Release / Unrestricted Use'), ('rework', 'Rework Required'), ('reject', 'Reject'), ('hold', 'Hold / Investigate')], max_length=20)),
                ('decision_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('decision_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quality_lots_assigned', to=settings.AUTH_USER_MODEL)),
                ('bmr', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quality_lots', to='bmr.bmr')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quality_lots_created', to=settings.AUTH_USER_MODEL)),
                ('decision_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quality_lots_decided', to=settings.AUTH_USER_MODEL)),
                ('phase_execution', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quality_lot', to='workflow.batchphaseexecution')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quality_lots', to='products.product')),
            ],
            options={
                'verbose_name': 'Quality Inspection Lot',
                'verbose_name_plural': 'Quality Inspection Lots',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='QualityInspectionCharacteristic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('test_method', models.CharField(blank=True, max_length=200)),
                ('specification', models.CharField(max_length=255)),
                ('lower_limit', models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ('upper_limit', models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ('unit', models.CharField(blank=True, max_length=30)),
                ('required', models.BooleanField(default=True)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('lot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='characteristics', to='dashboards.qualityinspectionlot')),
            ],
            options={
                'verbose_name': 'Quality Inspection Characteristic',
                'verbose_name_plural': 'Quality Inspection Characteristics',
                'ordering': ['lot', 'order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='QualityResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value_text', models.CharField(blank=True, max_length=255)),
                ('numeric_value', models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ('passed', models.BooleanField(blank=True, null=True)),
                ('comments', models.TextField(blank=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('characteristic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='dashboards.qualityinspectioncharacteristic')),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Quality Result',
                'verbose_name_plural': 'Quality Results',
                'ordering': ['-recorded_at'],
            },
        ),
        migrations.CreateModel(
            name='QualityDefect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('defect_type', models.CharField(choices=[('out_of_specification', 'Out of Specification'), ('deviation', 'Deviation'), ('documentation', 'Documentation Issue'), ('contamination', 'Contamination'), ('other', 'Other')], max_length=30)),
                ('severity', models.CharField(choices=[('minor', 'Minor'), ('major', 'Major'), ('critical', 'Critical')], default='major', max_length=20)),
                ('status', models.CharField(choices=[('open', 'Open'), ('investigating', 'Investigating'), ('corrective_action', 'Corrective Action'), ('closed', 'Closed')], default='open', max_length=30)),
                ('description', models.TextField()),
                ('corrective_action', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('closed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quality_defects_closed', to=settings.AUTH_USER_MODEL)),
                ('lot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='defects', to='dashboards.qualityinspectionlot')),
                ('reported_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quality_defects_reported', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Quality Defect',
                'verbose_name_plural': 'Quality Defects',
                'ordering': ['-created_at'],
            },
        ),
    ]
