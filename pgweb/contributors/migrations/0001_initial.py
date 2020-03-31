# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contributor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lastname', models.CharField(max_length=100)),
                ('firstname', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('company', models.CharField(max_length=100, null=True, blank=True)),
                ('companyurl', models.URLField(max_length=100, null=True, verbose_name='Company URL', blank=True)),
                ('location', models.CharField(max_length=100, null=True, blank=True)),
                ('contribution', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('lastname', 'firstname'),
            },
        ),
        migrations.CreateModel(
            name='ContributorType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('typename', models.CharField(max_length=32)),
                ('sortorder', models.IntegerField(default=100)),
                ('extrainfo', models.TextField(null=True, blank=True)),
                ('detailed', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('sortorder',),
            },
        ),
        migrations.AddField(
            model_name='contributor',
            name='ctype',
            field=models.ForeignKey(to='contributors.ContributorType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='contributor',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
    ]
