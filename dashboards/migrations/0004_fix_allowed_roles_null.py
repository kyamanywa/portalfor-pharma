# Generated migration for fixing allowed_roles NULL values

from django.db import migrations

def fix_allowed_roles_null_values(apps, schema_editor):
    """Ensure all DashboardPermission records have proper allowed_roles values"""
    DashboardPermission = apps.get_model('dashboards', 'DashboardPermission')
    
    for permission in DashboardPermission.objects.all():
        if permission.allowed_roles is None:
            permission.allowed_roles = []
            permission.save(update_fields=['allowed_roles'])

def reverse_fix_allowed_roles(apps, schema_editor):
    """Reverse migration - no action needed"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0002_dashboardpermission'),
    ]

    operations = [
        migrations.RunPython(
            fix_allowed_roles_null_values,
            reverse_fix_allowed_roles
        ),
    ]