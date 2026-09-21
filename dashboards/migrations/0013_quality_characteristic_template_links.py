from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bmr', '0019_historicalbmr'),
        ('dashboards', '0012_quality_management'),
    ]

    operations = [
        migrations.AddField(
            model_name='qualityinspectioncharacteristic',
            name='template_field',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quality_characteristics', to='bmr.bmrtemplatefield'),
        ),
        migrations.AddField(
            model_name='qualityinspectioncharacteristic',
            name='template_section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quality_characteristics', to='bmr.bmrtemplatesection'),
        ),
    ]
