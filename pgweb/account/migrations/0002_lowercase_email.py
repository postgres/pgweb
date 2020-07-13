# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL("UPDATE auth_user SET email=lower(email) WHERE email!=lower(email)"),
        migrations.RunSQL("ALTER TABLE auth_user ADD CONSTRAINT email_must_be_lowercase CHECK (email=lower(email))"),
        migrations.RunSQL("CREATE UNIQUE INDEX auth_user_email_lower_key ON auth_user USING btree(lower(email))"),
    ]
