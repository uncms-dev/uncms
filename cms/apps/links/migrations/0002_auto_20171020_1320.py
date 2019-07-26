# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-20 12:20
import cms.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='link',
            name='link_url',
            field=cms.models.fields.LinkField(help_text='The URL where the user will be redirected.', max_length=1000, verbose_name='link URL'),
        ),
        migrations.AlterField(
            model_name='link',
            name='new_window',
            field=models.BooleanField(default=False, help_text='Open the page in a new window.'),
        ),
    ]
