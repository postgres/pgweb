from django.contrib import admin
from django import forms

from models import *

class FeatureInline(admin.TabularInline):
	model = Feature

class FeatureGroupAdmin(admin.ModelAdmin):
	inlines = [FeatureInline, ]

class FeatureAdmin(admin.ModelAdmin):
	list_display = ('featurename', 'group')

admin.site.register(FeatureGroup, FeatureGroupAdmin)
admin.site.register(Feature, FeatureAdmin)
