# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('featurematrix', '0002_featurematrix_96'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='v10',
            field=models.IntegerField(default=0, verbose_name='10', choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')]),
        ),
        migrations.RunSQL("UPDATE featurematrix_feature SET v10=v96 WHERE NOT v10=v96"),
    ]
