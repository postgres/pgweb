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
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('catname', models.CharField(max_length=100)),
                ('blurb', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('catname',),
            },
        ),
        migrations.CreateModel(
            name='LicenceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('typename', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ('typename',),
            },
        ),
        migrations.CreateModel(
            name='Mirror',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country_name', models.CharField(max_length=50)),
                ('country_code', models.CharField(max_length=2)),
                ('mirror_created', models.DateTimeField(auto_now_add=True)),
                ('mirror_last_rsync', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0))),
                ('mirror_index', models.IntegerField()),
                ('host_addr', models.GenericIPAddressField(default='0.0.0.0', null=True)),
                ('host_path', models.CharField(max_length=100, null=True)),
                ('host_sponsor', models.CharField(max_length=100, null=True)),
                ('host_contact', models.CharField(max_length=100, null=True)),
                ('host_email', models.CharField(max_length=100, null=True)),
                ('host_notes', models.TextField(null=True)),
                ('rsync_host1', models.CharField(max_length=100, null=True)),
                ('rsync_host2', models.CharField(max_length=100, null=True)),
                ('mirror_active', models.BooleanField(default=True)),
                ('mirror_dns', models.BooleanField(default=False)),
                ('mirror_private', models.BooleanField(default=False)),
                ('host_use_cname', models.BooleanField(default=False)),
                ('host_cname_host', models.CharField(max_length=100, null=True)),
                ('mirror_primary', models.BooleanField(default=False)),
                ('error_count', models.IntegerField(default=0)),
                ('alternate_protocol', models.BooleanField(default=False)),
                ('alternate_at_root', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'mirrors',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('approved', models.BooleanField(default=False)),
                ('url', models.URLField()),
                ('description', models.TextField()),
                ('price', models.CharField(max_length=200, blank=True)),
                ('lastconfirmed', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(to='downloads.Category')),
                ('licencetype', models.ForeignKey(verbose_name='Licence type', to='downloads.LicenceType')),
                ('org', models.ForeignKey(db_column='publisher_id', verbose_name='Organisation', to='core.Organisation')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='StackBuilderApp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('textid', models.CharField(max_length=100)),
                ('version', models.CharField(max_length=20)),
                ('platform', models.CharField(max_length=20, choices=[('windows', 'Windows (32-bit)'), ('windows-x64', 'Windows (64-bit)'), ('osx', 'Mac OS X'), ('linux', 'Linux (32-bit)'), ('linux-x64', 'Linux (64-bit)')])),
                ('secondaryplatform', models.CharField(blank=True, max_length=20, choices=[('', 'None'), ('windows', 'Windows (32-bit)'), ('windows-x64', 'Windows (64-bit)'), ('osx', 'Mac OS X'), ('linux', 'Linux (32-bit)'), ('linux-x64', 'Linux (64-bit)')])),
                ('name', models.CharField(max_length=500)),
                ('active', models.BooleanField(default=True)),
                ('description', models.TextField()),
                ('category', models.CharField(max_length=100)),
                ('pgversion', models.CharField(max_length=5, blank=True)),
                ('edbversion', models.CharField(max_length=5, blank=True)),
                ('format', models.CharField(max_length=5, choices=[('bin', 'Linux .bin'), ('app', 'Mac .app'), ('pkg', 'Mac .pkg'), ('mpkg', 'Mac .mpkg'), ('exe', 'Windows .exe'), ('msi', 'Windows .msi')])),
                ('installoptions', models.CharField(max_length=500, blank=True)),
                ('upgradeoptions', models.CharField(max_length=500, blank=True)),
                ('checksum', models.CharField(max_length=32)),
                ('mirrorpath', models.CharField(max_length=500, blank=True)),
                ('alturl', models.URLField(max_length=500, blank=True)),
                ('txtdependencies', models.CharField(help_text='Comma separated list of text dependencies, no spaces!', max_length=1000, verbose_name='Dependencies', blank=True)),
                ('versionkey', models.CharField(max_length=500)),
                ('manifesturl', models.URLField(max_length=500, blank=True)),
            ],
            options={
                'ordering': ('textid', 'name', 'platform'),
            },
        ),
        migrations.AlterUniqueTogether(
            name='stackbuilderapp',
            unique_together=set([('textid', 'version', 'platform')]),
        ),
    ]
