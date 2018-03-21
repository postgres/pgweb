# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings

import pgweb.core.models

class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('tld', models.CharField(max_length=3)),
            ],
            options={
                'ordering': ('name',),
                'db_table': 'countries',
                'verbose_name': 'Country',
                'verbose_name_plural': 'Countries',
            },
        ),
        migrations.CreateModel(
            name='ImportedRSSFeed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('internalname', models.CharField(unique=True, max_length=32)),
                ('url', models.URLField()),
                ('purgepattern', models.CharField(help_text=b"NOTE! Pattern will be automatically anchored with ^ at the beginning, but you must lead with a slash in most cases - and don't forget to include the trailing $ in most cases", max_length=512, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ImportedRSSItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('posttime', models.DateTimeField()),
                ('feed', models.ForeignKey(to='core.ImportedRSSFeed')),
            ],
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('alpha3', models.CharField(max_length=7, serialize=False, primary_key=True)),
                ('alpha3term', models.CharField(max_length=3, blank=True)),
                ('alpha2', models.CharField(max_length=2, blank=True)),
                ('name', models.CharField(max_length=100)),
                ('frenchname', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ModerationNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('objectid', models.IntegerField(db_index=True)),
                ('objecttype', models.CharField(max_length=100)),
                ('text', models.TextField()),
                ('author', models.CharField(max_length=100)),
                ('date', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('-date',),
            },
        ),
        migrations.CreateModel(
            name='Organisation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('approved', models.BooleanField(default=False)),
                ('address', models.TextField(blank=True)),
                ('url', models.URLField()),
                ('email', models.EmailField(max_length=254, blank=True)),
                ('phone', models.CharField(max_length=100, blank=True)),
                ('lastconfirmed', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='OrganisationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('typename', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('sshkey', models.TextField(help_text=b'Paste one or more public keys in OpenSSH format, one per line.', verbose_name=b'SSH key', blank=True, validators=[pgweb.core.models.validate_sshkey])),
                ('lastmodified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tree', models.DecimalField(unique=True, max_digits=3, decimal_places=1)),
                ('latestminor', models.IntegerField(default=0, help_text=b"For testing versions, latestminor means latest beta/rc number. For other releases, it's the latest minor release number in the tree.")),
                ('reldate', models.DateField()),
                ('relnotes', models.CharField(max_length=32)),
                ('current', models.BooleanField(default=False)),
                ('supported', models.BooleanField(default=True)),
                ('testing', models.IntegerField(default=0, help_text=b'Testing level of this release. latestminor indicates beta/rc number', choices=[(0, b'Release'), (1, b'Release candidate'), (2, b'Beta'), (3, b'Alpha')])),
                ('docsloaded', models.DateTimeField(help_text=b'The timestamp of the latest docs load. Used to control indexing and info on developer docs.', null=True, blank=True)),
                ('firstreldate', models.DateField(help_text=b'The date of the .0 release in this tree')),
                ('eoldate', models.DateField(help_text=b'The planned EOL date for this tree')),
            ],
            options={
                'ordering': ('-tree',),
            },
        ),
        migrations.AddField(
            model_name='organisation',
            name='managers',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='organisation',
            name='orgtype',
            field=models.ForeignKey(verbose_name=b'Organisation type', to='core.OrganisationType'),
        ),
    ]
