from django.db import migrations, models


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('bmr', '0008_unique_batch_per_product'),
    ]

    operations = [
        migrations.CreateModel(
            name='BMRTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(blank=True, max_length=140, unique=True)),
                ('description', models.TextField(blank=True)),
                ('structure', models.JSONField(blank=True, default=list, help_text='JSON schema defining pages, sections, tables, and placeholders')),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-is_active', '-updated_at'],
                'verbose_name': 'BMR Template',
                'verbose_name_plural': 'BMR Templates',
            },
        ),
        migrations.AddField(
            model_name='bmr',
            name='template',
            field=models.ForeignKey(blank=True, help_text='Template structure used to render this BMR', null=True, on_delete=models.SET_NULL, related_name='bmrs', to='bmr.bmrtemplate'),
        ),
    ]