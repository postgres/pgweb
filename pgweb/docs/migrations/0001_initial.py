# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.DecimalField(max_digits=3, decimal_places=1)),
                ('file', models.CharField(max_length=64)),
                ('comment', models.TextField()),
                ('posted_at', models.DateTimeField(auto_now_add=True)),
                ('approved', models.BooleanField(default=False)),
                ('submitter', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-posted_at',),
            },
        ),
        migrations.CreateModel(
            name='DocPage',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('file', models.CharField(max_length=64)),
                ('title', models.CharField(max_length=256, null=True, blank=True)),
                ('content', models.TextField(null=True, blank=True)),
                ('version', models.ForeignKey(to='core.Version', db_column='version', to_field='tree')),
            ],
            options={
                'db_table': 'docs',
            },
        ),
        migrations.AlterUniqueTogether(
            name='docpage',
            unique_together=set([('file', 'version')]),
        ),
    ]
