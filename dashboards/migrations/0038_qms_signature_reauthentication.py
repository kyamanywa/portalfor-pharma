from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0037_alter_notificationsettings_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='qmselectronicsignature',
            name='reauthenticated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='qmselectronicsignature',
            name='reauthenticated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
