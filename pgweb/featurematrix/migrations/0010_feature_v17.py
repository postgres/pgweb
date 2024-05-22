# Generated by Django 3.2.10 on 2024-05-22 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('featurematrix', '0009_feature_v16'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='v17',
            field=models.IntegerField(choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')], default=0, verbose_name='17'),
        ),
        migrations.RunSQL("UPDATE featurematrix_feature SET v17=v16"),
    ]
