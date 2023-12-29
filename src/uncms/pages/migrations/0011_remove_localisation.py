from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0010_auto_20200812_1546"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="page",
            unique_together=set([("parent", "slug")]),
        ),
        migrations.RemoveField(
            model_name="country",
            name="group",
        ),
        migrations.RemoveField(
            model_name="page",
            name="country_group",
        ),
        migrations.RemoveField(
            model_name="page",
            name="is_content_object",
        ),
        migrations.RemoveField(
            model_name="page",
            name="owner",
        ),
        migrations.DeleteModel(
            name="Country",
        ),
        migrations.DeleteModel(
            name="CountryGroup",
        ),
    ]
