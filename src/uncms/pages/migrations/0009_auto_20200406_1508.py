from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0008_auto_20191108_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='slug',
            field=models.SlugField(help_text='A unique portion of the URL that is used to identify this specific page using human-readable keywords (e.g., about-us)', max_length=150),
        ),
    ]
