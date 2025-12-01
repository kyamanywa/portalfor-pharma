# Generated migration for ProductTypeConfiguration model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workflow', '0023_machine_phases'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductTypeConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type_key', models.CharField(help_text="System identifier for this product type (e.g., 'tablet_type_3'). Use lowercase, no spaces.", max_length=50, unique=True)),
                ('product_type_display', models.CharField(help_text='Human-readable name for display in UI (e.g., "Liquid Injection")', max_length=100)),
                ('description', models.TextField(blank=True, help_text='Optional description of this product type and its workflow')),
                ('default_packing_phase', models.CharField(blank=True, help_text="Default packing phase code for rollback scenarios (e.g., 'blister_packing')", max_length=50)),
                ('is_active', models.BooleanField(default=True, help_text='Enable/disable this product type across the system')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Product Type Configuration',
                'verbose_name_plural': 'Product Type Configurations',
                'ordering': ['product_type_display'],
            },
        ),
    ]
