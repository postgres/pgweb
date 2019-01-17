from django.contrib import admin
from django import forms
from django.forms import ValidationError

import re

from pgweb.util.admin import PgwebAdmin
from models import StackBuilderApp, Category, Product, LicenceType

class ProductAdmin(PgwebAdmin):
    list_display = ('name', 'org', 'approved', 'lastconfirmed',)
    list_filter = ('approved',)
    search_fields = ('name', 'description', )
    ordering = ('name', )

def duplicate_stackbuilderapp(modeladmin, request, queryset):
    # Duplicate each individual selected object, but turn off
    # the active flag if it's on.
    for o in queryset:
        o.id = None # Triggers creation of a new object
        o.active = False
        o.textid = o.textid + "_new"
        o.save()

duplicate_stackbuilderapp.short_description = "Duplicate application"

class StackBuilderAppAdminForm(forms.ModelForm):
    class Meta:
        model = StackBuilderApp
        exclude = ()

    def clean_textid(self):
        if not re.match('^[a-z0-9_]*$', self.cleaned_data['textid']):
            raise ValidationError('Only lowerchase characters, numbers and underscore allowed!')
        return self.cleaned_data['textid']

    def clean_txtdependencies(self):
        if len(self.cleaned_data['txtdependencies']) == 0:
            return ''

        deplist = self.cleaned_data['txtdependencies'].split(',')
        if len(deplist) != len(set(deplist)):
            raise ValidationError('Duplicate dependencies not allowed!')

        for d in deplist:
            if not StackBuilderApp.objects.filter(textid=d).exists():
                raise ValidationError("Dependency '%s' does not exist!" % d)
        return self.cleaned_data['txtdependencies']

class StackBuilderAppAdmin(admin.ModelAdmin):
    list_display = ('textid', 'active', 'name', 'platform', 'version', )
    actions = [duplicate_stackbuilderapp, ]
    form = StackBuilderAppAdminForm

admin.site.register(Category)
admin.site.register(LicenceType)
admin.site.register(Product, ProductAdmin)
admin.site.register(StackBuilderApp, StackBuilderAppAdmin)
