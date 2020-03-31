# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.CharField(max_length=500)),
                ('opt1', models.CharField(max_length=500)),
                ('opt2', models.CharField(max_length=500)),
                ('opt3', models.CharField(max_length=500, blank=True)),
                ('opt4', models.CharField(max_length=500, blank=True)),
                ('opt5', models.CharField(max_length=500, blank=True)),
                ('opt6', models.CharField(max_length=500, blank=True)),
                ('opt7', models.CharField(max_length=500, blank=True)),
                ('opt8', models.CharField(max_length=500, blank=True)),
                ('posted', models.DateTimeField(auto_now_add=True)),
                ('current', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='SurveyLock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ipaddr', models.GenericIPAddressField()),
                ('time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='SurveyAnswer',
            fields=[
                ('survey', models.OneToOneField(primary_key=True, serialize=False, to='survey.Survey', on_delete=models.CASCADE)),
                ('tot1', models.IntegerField(default=0)),
                ('tot2', models.IntegerField(default=0)),
                ('tot3', models.IntegerField(default=0)),
                ('tot4', models.IntegerField(default=0)),
                ('tot5', models.IntegerField(default=0)),
                ('tot6', models.IntegerField(default=0)),
                ('tot7', models.IntegerField(default=0)),
                ('tot8', models.IntegerField(default=0)),
            ],
        ),
    ]
