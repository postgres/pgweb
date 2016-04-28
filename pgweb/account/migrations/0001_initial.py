# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunityAuthSite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b"Note that the value in this field is shown on the login page, so make sure it's user-friendly!", max_length=100)),
                ('redirecturl', models.URLField()),
                ('cryptkey', models.CharField(help_text=b'Use tools/communityauth/generate_cryptkey.py to create a key', max_length=100)),
                ('comment', models.TextField(blank=True)),
                ('cooloff_hours', models.IntegerField(default=0, help_text=b'Number of hours a user must have existed in the systems before allowed to log in to this site')),
            ],
        ),
        migrations.CreateModel(
            name='EmailChangeToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75)),
                ('token', models.CharField(max_length=100)),
                ('sentat', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
