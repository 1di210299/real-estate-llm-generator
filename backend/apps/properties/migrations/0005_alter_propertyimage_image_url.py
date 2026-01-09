# Generated manually on 2026-01-09 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0004_property_date_listed_property_internal_property_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='propertyimage',
            name='image_url',
            field=models.TextField(help_text='Image URL - no length limit to support URLs with many parameters'),
        ),
    ]
