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
            field=models.BooleanField(default=False, help_text='Choose "Community event" if this is a community recognized event following the <a href="/about/policies/conferences/" target="_blank" rel="noopener">community event guidelines</a>.', verbose_name='Community event'),
        ),
        migrations.AddField(
            model_name='event',
            name='description_for_badged',
            field=models.TextField(help_text='DEPRECRATED: This was used in the beginning of community events to collect additional information.', null=True, blank=True, verbose_name='Description for community event'),
        ),
    ]
