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
    autocomplete_fields = ['user', ]
    list_display = ('__str__', 'user', 'ctype',)
    list_filter = ('ctype',)
    ordering = ('firstname', 'lastname',)
    search_fields = ('firstname', 'lastname', 'user__username',)


admin.site.register(ContributorType)
admin.site.register(Contributor, ContributorAdmin)
