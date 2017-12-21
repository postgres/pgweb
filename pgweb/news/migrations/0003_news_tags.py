# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_news_tweet'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('urlname', models.CharField(unique=True, max_length=20)),
                ('name', models.CharField(max_length=32)),
                ('description', models.CharField(max_length=200)),
            ],
            options={'ordering': ('urlname',)},
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='tweeted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='newsarticle',
            name='tags',
            field=models.ManyToManyField(help_text=b'Hover mouse over tags to view full description', to='news.NewsTag'),
        ),
    ]
