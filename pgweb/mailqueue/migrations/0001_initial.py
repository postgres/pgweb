# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='QueuedMail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sender', models.EmailField(max_length=100)),
                ('receiver', models.EmailField(max_length=100)),
                ('fullmsg', models.TextField()),
                ('usergenerated', models.BooleanField(default=False)),
            ],
        ),
    ]
