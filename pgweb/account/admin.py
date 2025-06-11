from django.contrib import admin
from django.core.validators import ValidationError
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django import forms

import base64
import re

from pgweb.util.widgets import TemplateRenderWidget
from pgweb.util.db import exec_to_dict
from pgweb.account.views import OAUTH_PASSWORD_STORE

from .models import CommunityAuthSite, CommunityAuthOrg, SecondaryEmail


class CommunityAuthSiteAdminForm(forms.ModelForm):
    class Meta:
        model = CommunityAuthSite
        exclude = ()

    def clean_cryptkey(self):
        x = None
        try:
            x = base64.b64decode(self.cleaned_data['cryptkey'])
        except Exception:
            raise forms.ValidationError("Crypto key must be base64 encoded")

        if (len(x) != 16 and len(x) != 24 and len(x) != 32 and len(x) != 64):
            raise forms.ValidationError("Crypto key must be 16, 24, 32 or 64 bytes before being base64-encoded")
        return self.cleaned_data['cryptkey']

    def clean(self):
        d = super().clean()

        if d.get('push_changes', False) and not d.get('apiurl', ''):
            self.add_error('push_changes', 'API url must be specified to enable push changes!')

        if d.get('push_ssh', False) and not d.get('push_changes', False):
            self.add_error('push_ssh', 'SSH changes can only be pushed if general change push is enabled')

        if d.get('cooloff_hours', 0) > 0 and not d.get('cooloff_message', ''):
            self.add_error('cooloff_message', 'Cooloff message must be specified if cooloff period is')

        return d


class CommunityAuthSiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'cooloff_hours', 'push_changes', 'push_ssh', 'org')
    form = CommunityAuthSiteAdminForm


class PGUserChangeForm(UserChangeForm):
    passwordinfo = forms.CharField(label="Password information", required=False)
    logininfo = forms.CharField(label="Community login history", required=False)
    extraemail = forms.CharField(label="Additional email addresses", required=False)

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

        self.fields['email'].help_text = "Be EXTREMELY careful when changing an email address! It is almost ALWAYS better to reset the password on the user and have them change it on their own! Sync issues are common!"
        self.fields['extraemail'].widget = TemplateRenderWidget(
            template='forms/widgets/extra_email_list_widget.html',
            context={
                'emails': SecondaryEmail.objects.filter(user=self.instance).order_by('-confirmed', 'email'),
            },
        )

    def password_type(self, obj):
        if obj.password == OAUTH_PASSWORD_STORE:
            return "OAuth integrated"
        elif obj.password.startswith('pbkdf2_'):
            return "Regular password"
        elif obj.password.startswith('sha1$'):
            return "Old SHA1 password"
        elif re.match('^[a-z0-9]{64}', obj.password):
            return "Old unknown hash"
        else:
            return "Unknown"

    def clean_email(self):
        e = self.cleaned_data['email'].lower()
        if User.objects.filter(email=e).exclude(pk=self.instance.pk):
            raise ValidationError("There already exists a different user with this address")
        if SecondaryEmail.objects.filter(email=e):
            raise ValidationError("This address is already a secondary address attached to a user")

        return e


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
        if 'extraemail' not in fs[1][1]['fields']:
            fs[1][1]['fields'] = list(fs[1][1]['fields']) + ['extraemail', ]
        return fs

    def has_view_permission(self, request, obj=None):
        """
        We have a special check for view permissions here based on if the user
        has access to modifying contributors. This allows us to allow the
        editor to return a list of usernames from the dropdown. If this is not
        the autocomplete / user editor workflow, then we proceed as normal.
        """
        if request.path == '/admin/autocomplete/' and request.GET.get('app_label') == 'contributors' and request.GET.get('model_name') == 'contributor' and request.user.has_perm("contributors.change_contributor"):
            return True
        return super().has_view_permission(request, obj)

    @property
    def search_fields(self):
        sf = list(super().search_fields)
        return sf + ['secondaryemail__email', ]


admin.site.register(CommunityAuthSite, CommunityAuthSiteAdmin)
admin.site.register(CommunityAuthOrg)
admin.site.unregister(User)  # have to unregister default User Admin...
admin.site.register(User, PGUserAdmin)  # ...in order to add overrides
