from django.db import migrations


def clear_capsule_default_packing_phase(apps, schema_editor):
    ProductTypeConfiguration = apps.get_model('workflow', 'ProductTypeConfiguration')
    ProductTypeConfiguration.objects.filter(
        product_type_key__iexact='capsule'
    ).update(default_packing_phase='')


def restore_capsule_default_packing_phase(apps, schema_editor):
    ProductTypeConfiguration = apps.get_model('workflow', 'ProductTypeConfiguration')
    ProductTypeConfiguration.objects.filter(
        product_type_key__iexact='capsule'
    ).update(default_packing_phase='filling')


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0037_alter_productionphase_phase_name'),
    ]

    operations = [
        migrations.RunPython(
            clear_capsule_default_packing_phase,
            restore_capsule_default_packing_phase,
        ),
    ]
