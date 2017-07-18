# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0002_hide_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contributor',
            name='email',
            field=models.EmailField(null=False, blank=True),
        ),
    ]
