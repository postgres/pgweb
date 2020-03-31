# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32)),
                ('dedicated', models.BooleanField(default=True)),
                ('performance', models.CharField(max_length=128)),
                ('os', models.CharField(max_length=32)),
                ('location', models.CharField(max_length=128)),
                ('usage', models.TextField()),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Sponsor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('url', models.URLField()),
                ('logoname', models.CharField(max_length=64)),
                ('country', models.ForeignKey(to='core.Country', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='SponsorType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('typename', models.CharField(max_length=32)),
                ('description', models.TextField()),
                ('sortkey', models.IntegerField(default=10)),
            ],
            options={
                'ordering': ('sortkey',),
            },
        ),
        migrations.AddField(
            model_name='sponsor',
            name='sponsortype',
            field=models.ForeignKey(to='sponsors.SponsorType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='server',
            name='sponsors',
            field=models.ManyToManyField(to='sponsors.Sponsor'),
        ),
    ]
