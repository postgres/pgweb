# Generated by Django 2.2.12 on 2020-08-30 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('featurematrix', '0005_feature_v12'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='v13',
            field=models.IntegerField(choices=[(0, 'No'), (1, 'Yes'), (2, 'Obsolete'), (3, '?')], default=0, verbose_name='13'),
        ),
        migrations.RunSQL("UPDATE featurematrix_feature SET v13=v12"),
    ]