# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('featurematrix', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='v96',
            field=models.IntegerField(default=0, verbose_name='9.6', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')]),
        ),
        migrations.RunSQL("UPDATE featurematrix_feature SET v96=v95 WHERE NOT v96=v95"),
    ]
