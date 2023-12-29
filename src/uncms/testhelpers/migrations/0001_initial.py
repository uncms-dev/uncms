# Generated by Django 4.1.7 on 2023-03-13 04:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("pages", "0011_remove_localisation"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmptyTestPage",
            fields=[
                (
                    "page",
                    models.OneToOneField(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="+",
                        serialize=False,
                        to="pages.page",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
