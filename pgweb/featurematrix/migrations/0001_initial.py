# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('featurename', models.CharField(max_length=100)),
                ('featuredescription', models.TextField(blank=True, help_text="""Supports Markdown. A single, plain URL will link directly to that URL.""")),
                ('v74', models.IntegerField(default=0, verbose_name='7.4', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v80', models.IntegerField(default=0, verbose_name='8.0', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v81', models.IntegerField(default=0, verbose_name='8.1', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v82', models.IntegerField(default=0, verbose_name='8.2', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v83', models.IntegerField(default=0, verbose_name='8.3', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v84', models.IntegerField(default=0, verbose_name='8.4', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v90', models.IntegerField(default=0, verbose_name='9.0', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v91', models.IntegerField(default=0, verbose_name='9.1', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v92', models.IntegerField(default=0, verbose_name='9.2', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v93', models.IntegerField(default=0, verbose_name='9.3', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v94', models.IntegerField(default=0, verbose_name='9.4', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
                ('v95', models.IntegerField(default=0, verbose_name='9.5', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')])),
            ],
        ),
        migrations.CreateModel(
            name='FeatureGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('groupname', models.CharField(max_length=100)),
                ('groupsort', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='feature',
            name='group',
            field=models.ForeignKey(to='featurematrix.FeatureGroup', on_delete=models.CASCADE),
        ),
    ]
