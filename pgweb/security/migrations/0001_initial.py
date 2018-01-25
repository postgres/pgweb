# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import pgweb.security.models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_news_tags'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityPatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('public', models.BooleanField(default=False)),
                ('cve', models.CharField(blank=True, max_length=32, validators=[pgweb.security.models.cve_validator])),
                ('cvenumber', models.IntegerField(db_index=True)),
                ('detailslink', models.URLField(blank=True)),
                ('description', models.TextField()),
                ('component', models.CharField(help_text=b'If multiple components, choose the most critical one', max_length=32, choices=[(b'core server', b'Core server product'), (b'client', b'Client library or application only'), (b'contrib module', b'Contrib module only'), (b'client contrib module', b'Client contrib module only'), (b'packaging', b'Packaging, e.g. installers or RPM'), (b'other', b'Other')])),
                ('vector_av', models.CharField(blank=True, max_length=1, verbose_name=b'Attack Vector', choices=[('N', 'Network'), ('A', 'Adjacent'), ('L', 'Local'), ('P', 'Physical')])),
                ('vector_ac', models.CharField(blank=True, max_length=1, verbose_name=b'Attack Complexity', choices=[('L', 'Low'), ('H', 'High')])),
                ('vector_pr', models.CharField(blank=True, max_length=1, verbose_name=b'Privileges Required', choices=[('N', 'None'), ('L', 'Low'), ('H', 'High')])),
                ('vector_ui', models.CharField(blank=True, max_length=1, verbose_name=b'User Interaction', choices=[('N', 'None'), ('R', 'Required')])),
                ('vector_s', models.CharField(blank=True, max_length=1, verbose_name=b'Scope', choices=[('C', 'Changed'), ('U', 'Unchanged')])),
                ('vector_c', models.CharField(blank=True, max_length=1, verbose_name=b'Confidentiality Impact', choices=[('H', 'High'), ('L', 'Low'), ('N', 'None')])),
                ('vector_i', models.CharField(blank=True, max_length=1, verbose_name=b'Integrity Impact', choices=[('H', 'High'), ('L', 'Low'), ('N', 'None')])),
                ('vector_a', models.CharField(blank=True, max_length=1, verbose_name=b'Availability Impact', choices=[('H', 'High'), ('L', 'Low'), ('N', 'None')])),
                ('legacyscore', models.CharField(blank=True, max_length=1, verbose_name=b'Legacy score', choices=[(b'A', b'A'), (b'B', b'B'), (b'C', b'C'), (b'D', b'D')])),
                ('newspost', models.ForeignKey(blank=True, to='news.NewsArticle', null=True)),
            ],
            options={
                'ordering': ('-cvenumber',),
                'verbose_name_plural': 'Security patches',
            },
        ),
        migrations.CreateModel(
            name='SecurityPatchVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fixed_minor', models.IntegerField()),
                ('patch', models.ForeignKey(to='security.SecurityPatch')),
                ('version', models.ForeignKey(to='core.Version')),
            ],
        ),
        migrations.AddField(
            model_name='securitypatch',
            name='versions',
            field=models.ManyToManyField(to='core.Version', through='security.SecurityPatchVersion'),
        ),
    ]
