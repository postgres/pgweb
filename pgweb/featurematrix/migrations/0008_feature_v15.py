# Generated by Django 3.2.10 on 2022-05-14 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('featurematrix', '0007_feature_v14'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='v15',
            field=models.IntegerField(choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')], default=0, verbose_name='15'),
        ),
        migrations.RunSQL("UPDATE featurematrix_feature SET v15=v14"),
    ]
