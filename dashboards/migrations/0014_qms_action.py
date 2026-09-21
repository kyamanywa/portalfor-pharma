from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bmr', '0019_historicalbmr'),
        ('dashboards', '0013_quality_characteristic_template_links'),
        ('products', '0035_product_capsule_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='QMSAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qms_number', models.CharField(blank=True, max_length=30, unique=True)),
                ('category', models.CharField(choices=[('deviation', 'Deviation / OOS Investigation'), ('capa', 'CAPA'), ('change_control', 'Change Control'), ('complaint', 'Complaint / Recall'), ('supplier_quality', 'Supplier Quality'), ('stability', 'Stability Study'), ('coa', 'Certificate of Analysis'), ('audit', 'Audit Finding'), ('document_control', 'SOP / Document Control'), ('risk', 'Quality Risk Management')], max_length=30)),
                ('owner_role', models.CharField(choices=[('qa', 'Quality Assurance'), ('qc', 'Quality Control')], db_index=True, max_length=10)),
                ('status', models.CharField(choices=[('open', 'Open'), ('investigation', 'Investigation'), ('action_required', 'Action Required'), ('pending_approval', 'Pending Approval'), ('closed', 'Closed'), ('cancelled', 'Cancelled')], db_index=True, default='open', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20)),
                ('title', models.CharField(max_length=180)),
                ('description', models.TextField()),
                ('root_cause', models.TextField(blank=True)),
                ('corrective_action', models.TextField(blank=True)),
                ('preventive_action', models.TextField(blank=True)),
                ('effectiveness_check', models.TextField(blank=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_actions_approved', to=settings.AUTH_USER_MODEL)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_actions_assigned', to=settings.AUTH_USER_MODEL)),
                ('bmr', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_actions', to='bmr.bmr')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_actions_created', to=settings.AUTH_USER_MODEL)),
                ('defect', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_actions', to='dashboards.qualitydefect')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_actions', to='products.product')),
                ('quality_lot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_actions', to='dashboards.qualityinspectionlot')),
            ],
            options={
                'verbose_name': 'QMS Action',
                'verbose_name_plural': 'QMS Actions',
                'ordering': ['-created_at'],
            },
        ),
    ]
