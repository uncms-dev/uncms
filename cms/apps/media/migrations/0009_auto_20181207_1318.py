# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-12-07 13:18
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0008_auto_20180801_1633'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='file',
            options={'ordering': ['-date_added', '-pk']},
        ),
        migrations.AddField(
            model_name='file',
            name='date_added',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
