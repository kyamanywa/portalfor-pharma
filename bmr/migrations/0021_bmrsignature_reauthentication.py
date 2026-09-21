from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmr', '0020_delete_historicalbmr'),
    ]

    operations = [
        migrations.AddField(
            model_name='bmrsignature',
            name='reauthenticated',
            field=models.BooleanField(default=False, help_text='Whether the signer re-entered their password for this critical action.'),
        ),
        migrations.AddField(
            model_name='bmrsignature',
            name='reauthenticated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='bmrsignature',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
