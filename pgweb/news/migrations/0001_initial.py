# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsArticle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approved', models.BooleanField(default=False)),
                ('date', models.DateField(default=datetime.date.today)),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('org', models.ForeignKey(verbose_name=b'Organisation', to='core.Organisation', help_text=b'If no organisations are listed, please check the <a href="/account/orglist/">organisation list</a> and contact the organisation manager or webmaster@postgresql.org if none are listed.')),
            ],
            options={
                'ordering': ('-date',),
            },
        ),
    ]
