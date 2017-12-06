# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='badged',
            field=models.BooleanField(default=False, help_text=b'Choose "Badged" if this is a community recognized event following the <a href="/community/recognition/#conferences" target="_blank">community event guidelines</a>.', verbose_name=b'Community event'),
        ),
        migrations.AddField(
            model_name='event',
            name='description_for_badged',
            field=models.TextField(help_text=b'Please describe how this is a community recognized event following the <a href="/community/recognition/#conferences" target="_blank">community event guidelines</a>. Please be as detailed as possible.', null=True, blank=True),
        ),
    ]
