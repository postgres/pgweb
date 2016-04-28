# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PUG',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approved', models.BooleanField(default=False)),
                ('locale', models.CharField(help_text=b"Locale where the PUG meets, e.g. 'New York City'", max_length=255)),
                ('title', models.CharField(help_text=b"Title/Name of the PUG, e.g. 'NYC PostgreSQL User Group'", max_length=255)),
                ('website_url', models.TextField(null=True, blank=True)),
                ('mailing_list_url', models.TextField(null=True, blank=True)),
                ('country', models.ForeignKey(to='core.Country')),
                ('org', models.ForeignKey(blank=True, to='core.Organisation', help_text=b'Organization that manages the PUG and its contents', null=True)),
            ],
        ),
    ]
