# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Quote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approved', models.BooleanField(default=False)),
                ('quote', models.TextField()),
                ('who', models.CharField(max_length=100)),
                ('org', models.CharField(max_length=100)),
                ('link', models.URLField()),
            ],
        ),
    ]
