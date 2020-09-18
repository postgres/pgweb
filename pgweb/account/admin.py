from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django import forms

import base64
import re

from pgweb.util.widgets import TemplateRenderWidget
from pgweb.util.db import exec_to_dict
from pgweb.account.views import OAUTH_PASSWORD_STORE

from .models import CommunityAuthSite, CommunityAuthOrg


class CommunityAuthSiteAdminForm(forms.ModelForm):
    class Meta:
        model = CommunityAuthSite
        exclude = ()

    def clean_cryptkey(self):
        x = None
        try:
            x = base64.b64decode(self.cleaned_data['cryptkey'])
        except TypeError:
            raise forms.ValidationError("Crypto key must be base64 encoded")

        if (len(x) != 16 and len(x) != 24 and len(x) != 32):
            raise forms.ValidationError("Crypto key must be 16, 24 or 32 bytes before being base64-encoded")
        return self.cleaned_data['cryptkey']

    def clean(self):
        d = super().clean()

        if d.get('push_changes', False) and not d['apiurl']:
            self.add_error('push_changes', 'API url must be specified to enable push changes!')

        if d.get('push_ssh', False) and not d.get('push_changes', False):
            self.add_error('push_ssh', 'SSH changes can only be pushed if general change push is enabled')

        return d


class CommunityAuthSiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'cooloff_hours', 'push_changes', 'push_ssh', 'org')
    form = CommunityAuthSiteAdminForm


class PGUserChangeForm(UserChangeForm):
    passwordinfo = forms.CharField(label="Password information", required=False)
    logininfo = forms.CharField(label="Community login history", required=False)

    def __init__(self, *args, **kwargs):
        super(PGUserChangeForm, self).__init__(*args, **kwargs)
        # because the auth.User model is set to "blank=False" and the Django
        # auth.UserChangeForm is setup as a ModelForm, it will always validate
        # the "username" even though it is not present.  Thus the best way to
        # avoid the validation is to remove the "username" field, if it exists
        if self.fields.get('username'):
            del self.fields['username']

        self.fields['passwordinfo'].widget = TemplateRenderWidget(
            template='forms/widgets/community_auth_password_info.html',
            context={
                'type': self.password_type(self.instance),
            },
        )

        self.fields['logininfo'].widget = TemplateRenderWidget(
            template='forms/widgets/community_auth_usage_widget.html',
            context={
                'logins': exec_to_dict("SELECT s.name AS service, lastlogin, logincount FROM account_communityauthsite s INNER JOIN account_communityauthlastlogin l ON s.id=l.site_id WHERE user_id=%(userid)s ORDER BY lastlogin DESC", {
                    'userid': self.instance.pk,
                }),
            })

    def password_type(self, obj):
        if obj.password == OAUTH_PASSWORD_STORE:
            return "OAuth integrated"
        elif obj.password.startswith('pbkdf2_'):
            return "Regular password"
        elif obj.password.startswith('sha1_'):
            return "Old SHA1 password"
        elif re.match('^[a-z0-9]{64}'):
            return "Old unknown hash"
        else:
            return "Unknown"


class PGUserAdmin(UserAdmin):
    """overrides default Django user admin"""
    form = PGUserChangeForm

    def get_readonly_fields(self, request, obj=None):
        """this prevents users from changing a username once created"""
        if obj:
            return self.readonly_fields + ('username',)
        return self.readonly_fields

    @property
    def fieldsets(self):
        fs = list(super().fieldsets)
        fs.append(
            ('Community authentication', {'fields': ('logininfo', )}),
        )
        if 'passwordinfo' not in fs[0][1]['fields']:
            fs[0][1]['fields'] = list(fs[0][1]['fields']) + ['passwordinfo', ]
        return fs


admin.site.register(CommunityAuthSite, CommunityAuthSiteAdmin)
admin.site.register(CommunityAuthOrg)
admin.site.unregister(User)  # have to unregister default User Admin...
admin.site.register(User, PGUserAdmin)  # ...in order to add overrides
