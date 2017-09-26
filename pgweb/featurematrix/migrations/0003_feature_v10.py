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
            field=models.IntegerField(default=0, verbose_name=b'10', choices=[(0, b'No'), (1, b'Yes'), (2, b'Obsolete'), (3, b'?')]),
        ),
		migrations.RunSQL("UPDATE featurematrix_feature SET v10=v96 WHERE NOT v10=v96"),
    ]
