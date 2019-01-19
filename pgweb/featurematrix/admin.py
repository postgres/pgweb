from django.contrib import admin

from .models import Feature, FeatureGroup


class FeatureInline(admin.TabularInline):
    model = Feature


class FeatureGroupAdmin(admin.ModelAdmin):
    inlines = [FeatureInline, ]
    list_display = ('groupname', 'groupsort')
    ordering = ['groupsort']


class FeatureAdmin(admin.ModelAdmin):
    list_display = ('featurename', 'group')
    list_filter = ('group',)
    search_fields = ('featurename',)


admin.site.register(FeatureGroup, FeatureGroupAdmin)
admin.site.register(Feature, FeatureAdmin)
