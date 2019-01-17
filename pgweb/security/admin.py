from django.contrib import admin
from django import forms
from django.conf import settings

from pgweb.core.models import Version
from pgweb.news.models import NewsArticle
from models import SecurityPatch, SecurityPatchVersion


class VersionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.numtree


class SecurityPatchVersionAdminForm(forms.ModelForm):
    model = SecurityPatchVersion
    version = VersionChoiceField(queryset=Version.objects.filter(tree__gt=0), required=True)


class SecurityPatchVersionAdmin(admin.TabularInline):
    model = SecurityPatchVersion
    extra = 2
    form = SecurityPatchVersionAdminForm


class SecurityPatchForm(forms.ModelForm):
    model = SecurityPatch
    newspost = forms.ModelChoiceField(queryset=NewsArticle.objects.filter(org=settings.PGDG_ORG_ID), required=False)

    def clean(self):
        d = super(SecurityPatchForm, self).clean()
        vecs = [v for k, v in d.items() if k.startswith('vector_')]
        empty = [v for v in vecs if v == '']
        if len(empty) != len(vecs) and len(empty) != 0:
            for k in d.keys():
                if k.startswith('vector_'):
                    self.add_error(k, 'Either specify all vector values or none')
        return d


class SecurityPatchAdmin(admin.ModelAdmin):
    form = SecurityPatchForm
    exclude = ['cvenumber', ]
    inlines = (SecurityPatchVersionAdmin, )
    list_display = ('cve', 'public', 'cvssscore', 'legacyscore', 'cvssvector', 'description')
    actions = ['make_public', 'make_unpublic']

    def cvssvector(self, obj):
        if not obj.cvssvector:
            return ''
        return '<a href="https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?vector={0}">{0}</a>'.format(
            obj.cvssvector)
    cvssvector.allow_tags = True
    cvssvector.short_description = "CVSS vector link"

    def cvssscore(self, obj):
        return obj.cvssscore
    cvssscore.short_description = "CVSS score"

    def make_public(self, request, queryset):
        self.do_public(queryset, True)

    def make_unpublic(self, request, queryset):
        self.do_public(queryset, False)

    def do_public(self, queryset, val):
        # Intentionally loop and do manually, so we generate change notices
        for p in queryset.all():
            p.public = val
            p.save()


admin.site.register(SecurityPatch, SecurityPatchAdmin)
