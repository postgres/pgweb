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
                ('featuredescription', models.TextField(blank=True)),
                ('v74', models.IntegerField(default=0, verbose_name=b'7.4', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v80', models.IntegerField(default=0, verbose_name=b'8.0', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v81', models.IntegerField(default=0, verbose_name=b'8.1', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v82', models.IntegerField(default=0, verbose_name=b'8.2', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v83', models.IntegerField(default=0, verbose_name=b'8.3', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v84', models.IntegerField(default=0, verbose_name=b'8.4', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v90', models.IntegerField(default=0, verbose_name=b'9.0', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v91', models.IntegerField(default=0, verbose_name=b'9.1', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v92', models.IntegerField(default=0, verbose_name=b'9.2', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v93', models.IntegerField(default=0, verbose_name=b'9.3', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v94', models.IntegerField(default=0, verbose_name=b'9.4', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
                ('v95', models.IntegerField(default=0, verbose_name=b'9.5', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')])),
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
            field=models.ForeignKey(to='featurematrix.FeatureGroup'),
        ),
    ]
