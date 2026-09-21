from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboards', '0015_qms_documents_deviations_risk'),
    ]

    operations = [
        migrations.CreateModel(
            name='QMSAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('audit_number', models.CharField(blank=True, max_length=30, unique=True)),
                ('audit_type', models.CharField(choices=[('internal', 'Internal Audit'), ('supplier', 'Supplier Audit'), ('regulatory', 'Regulatory Audit'), ('fda', 'FDA Audit'), ('iso', 'ISO Audit'), ('stores', 'Stores Audit')], db_index=True, max_length=20)),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('in_progress', 'In Progress'), ('finding_open', 'Finding Open'), ('corrective_action', 'Corrective Action'), ('pending_verification', 'Pending Verification'), ('closed', 'Closed')], db_index=True, default='planned', max_length=30)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20)),
                ('finding_type', models.CharField(choices=[('observation', 'Observation'), ('minor_nc', 'Minor Non-Conformance'), ('major_nc', 'Major Non-Conformance'), ('critical_nc', 'Critical Non-Conformance'), ('opportunity', 'Opportunity for Improvement')], default='observation', max_length=30)),
                ('title', models.CharField(max_length=180)),
                ('scope', models.TextField(blank=True)),
                ('auditee', models.CharField(blank=True, max_length=160)),
                ('department', models.CharField(blank=True, max_length=120)),
                ('standard_reference', models.CharField(blank=True, max_length=180)),
                ('observation', models.TextField(blank=True)),
                ('corrective_action', models.TextField(blank=True)),
                ('verification_notes', models.TextField(blank=True)),
                ('evidence_file', models.FileField(blank=True, null=True, upload_to='qms_audits/')),
                ('due_date', models.DateField(blank=True, null=True)),
                ('planned_date', models.DateField(blank=True, null=True)),
                ('conducted_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('closed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_audits_closed', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_audits_created', to=settings.AUTH_USER_MODEL)),
                ('qms_action', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audits', to='dashboards.qmsaction')),
                ('responsible_person', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qms_audits_responsible', to=settings.AUTH_USER_MODEL)),
                ('risk_assessment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audits', to='dashboards.qmsriskassessment')),
            ],
            options={
                'verbose_name': 'QMS Audit',
                'verbose_name_plural': 'QMS Audits',
                'ordering': ['-created_at'],
            },
        ),
    ]
