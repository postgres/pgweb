from django import forms
from django.contrib import admin

from .models import Contributor, ContributorType


class ContributorAdminForm(forms.ModelForm):
    class Meta:
        model = Contributor
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(ContributorAdminForm, self).__init__(*args, **kwargs)


class ContributorAdmin(admin.ModelAdmin):
    form = ContributorAdminForm


admin.site.register(ContributorType)
admin.site.register(Contributor, ContributorAdmin)
