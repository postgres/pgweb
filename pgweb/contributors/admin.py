from django import forms
from django.contrib import admin
from django.db.models import Count

from .models import Contributor, ContributorType, Badge, Badgeholder


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
    ordering = ('ctype', 'lastname', 'firstname')
    search_fields = ('firstname', 'lastname', 'user__username',)


class BadgeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slug', 'holders_count', 'approved', 'org',)
    list_filter = ('approved', 'org',)
    autocomplete_fields = ['holders', ]

    def holders_count(self, obj):
        return obj.holders_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(holders_count=Count("holders"))
        return queryset


admin.site.register(ContributorType)
admin.site.register(Contributor, ContributorAdmin)
admin.site.register(Badge, BadgeAdmin)
admin.site.register(Badgeholder)
