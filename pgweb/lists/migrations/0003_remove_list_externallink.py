# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lists', '0002_listname_unique'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mailinglist',
            name='externallink',
        ),
    ]
