# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='securitypatch',
            name='cve_visible',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='securitypatch',
            name='cve_visible',
            field=models.BooleanField(default=False),
        ),
    ]
