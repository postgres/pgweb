# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MailingList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('listname', models.CharField(max_length=64)),
                ('active', models.BooleanField(default=False)),
                ('externallink', models.URLField(null=True, blank=True)),
                ('description', models.TextField(blank=True)),
                ('shortdesc', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('listname',),
            },
        ),
        migrations.CreateModel(
            name='MailingListGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('groupname', models.CharField(max_length=64)),
                ('sortkey', models.IntegerField(default=10)),
            ],
            options={
                'ordering': ('sortkey',),
            },
        ),
        migrations.AddField(
            model_name='mailinglist',
            name='group',
            field=models.ForeignKey(to='lists.MailingListGroup'),
        ),
    ]
