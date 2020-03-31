# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfessionalService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approved', models.BooleanField(default=False)),
                ('description', models.TextField()),
                ('employees', models.CharField(max_length=32, null=True, blank=True)),
                ('locations', models.CharField(max_length=128, null=True, blank=True)),
                ('region_africa', models.BooleanField(default=False, verbose_name='Africa')),
                ('region_asia', models.BooleanField(default=False, verbose_name='Asia')),
                ('region_europe', models.BooleanField(default=False, verbose_name='Europe')),
                ('region_northamerica', models.BooleanField(default=False, verbose_name='North America')),
                ('region_oceania', models.BooleanField(default=False, verbose_name='Oceania')),
                ('region_southamerica', models.BooleanField(default=False, verbose_name='South America')),
                ('hours', models.CharField(max_length=128, null=True, blank=True)),
                ('languages', models.CharField(max_length=128, null=True, blank=True)),
                ('customerexample', models.TextField(null=True, verbose_name='Customer Example', blank=True)),
                ('experience', models.TextField(null=True, blank=True)),
                ('contact', models.TextField(null=True, blank=True)),
                ('url', models.URLField(max_length=128, null=True, verbose_name='URL', blank=True)),
                ('provides_support', models.BooleanField(default=False)),
                ('provides_hosting', models.BooleanField(default=False)),
                ('interfaces', models.CharField(max_length=512, null=True, verbose_name='Interfaces (for hosting)', blank=True)),
                ('org', models.OneToOneField(db_column='organisation_id', to='core.Organisation', help_text='If no organisations are listed, please check the <a href="/account/orglist/">organisation list</a> and contact the organisation manager or <a href="mailto:webmaster@postgresql.org">webmaster@postgresql.org</a> if none are listed.', verbose_name='organisation', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('org__name',),
            },
        ),
    ]
