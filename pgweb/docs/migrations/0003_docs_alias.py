# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0002_drop_doccomments'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocPageAlias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file1', models.CharField(unique=True, max_length=64)),
                ('file2', models.CharField(unique=True, max_length=64)),
            ],
            options={
                'db_table': 'docsalias',
                'verbose_name_plural': 'Doc page aliases',
            },
        ),
		migrations.RunSQL("CREATE UNIQUE INDEX docsalias_unique ON docsalias (LEAST(file1, file2), GREATEST(file1, file2))"),
    ]
