# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-15 15:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0006_auto_20151002_1655"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="page",
            name="cached_url",
        ),
    ]
