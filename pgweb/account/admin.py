from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django import forms

import base64

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


class CommunityAuthSiteAdmin(admin.ModelAdmin):
    form = CommunityAuthSiteAdminForm


class PGUserChangeForm(UserChangeForm):
    """just like UserChangeForm, butremoves "username" requirement"""
    def __init__(self, *args, **kwargs):
        super(PGUserChangeForm, self).__init__(*args, **kwargs)
        # because the auth.User model is set to "blank=False" and the Django
        # auth.UserChangeForm is setup as a ModelForm, it will always validate
        # the "username" even though it is not present.  Thus the best way to
        # avoid the validation is to remove the "username" field, if it exists
        if self.fields.get('username'):
            del self.fields['username']


class PGUserAdmin(UserAdmin):
    """overrides default Django user admin"""
    form = PGUserChangeForm

    def get_readonly_fields(self, request, obj=None):
        """this prevents users from changing a username once created"""
        if obj:
            return self.readonly_fields + ('username',)
        return self.readonly_fields


admin.site.register(CommunityAuthSite, CommunityAuthSiteAdmin)
admin.site.register(CommunityAuthOrg)
admin.site.unregister(User)  # have to unregister default User Admin...
admin.site.register(User, PGUserAdmin)  # ...in order to add overrides
