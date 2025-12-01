# Generated migration to make batch_number unique per product
from django.db import migrations, models
import bmr.models


class Migration(migrations.Migration):

    dependencies = [
        ('bmr', '0007_fix_bmr_request_cascade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bmr',
            name='batch_number',
            field=models.CharField(help_text='Enter batch number in format XXXYYYY (e.g., 3332025)', max_length=10, validators=[bmr.models.validate_batch_number]),
        ),
        migrations.AddConstraint(
            model_name='bmr',
            constraint=models.UniqueConstraint(fields=['product', 'batch_number'], name='unique_product_batch_number'),
        ),
    ]
