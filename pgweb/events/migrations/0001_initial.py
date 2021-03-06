# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pgweb.core.text import ORGANISATION_HINT_TEXT


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approved', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=100)),
                ('isonline', models.BooleanField(default=False, verbose_name='Online event')),
                ('city', models.CharField(max_length=50, blank=True)),
                ('state', models.CharField(max_length=50, blank=True)),
                ('training', models.BooleanField(default=False)),
                ('startdate', models.DateField(verbose_name='Start date')),
                ('enddate', models.DateField(verbose_name='End date')),
                ('summary', models.TextField(help_text='A short introduction (shown on the events listing page)')),
                ('details', models.TextField(help_text='Complete event description')),
                ('country', models.ForeignKey(blank=True, to='core.Country', null=True, on_delete=models.CASCADE)),
                ('language', models.ForeignKey(default='eng', blank=True, to='core.Language', help_text='Primary language for event. When multiple languages, specify this in the event description', null=True, on_delete=models.CASCADE)),
                ('org', models.ForeignKey(verbose_name='Organisation', to='core.Organisation', help_text=ORGANISATION_HINT_TEXT, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-startdate', '-enddate'),
            },
        ),
    ]
