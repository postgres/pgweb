from django.contrib import admin
from django import forms
from django.db import connection
from django.http import HttpResponseRedirect, HttpResponse

from pgweb.core.models import *

class OrganisationAdmin(admin.ModelAdmin):
	list_display = ('name', 'approved', 'lastconfirmed',)
	list_filter = ('approved',)
	ordering = ('name', )
	filter_horizontal = ('managers', )
	search_fields = ('name', )

class VersionAdmin(admin.ModelAdmin):
	list_display = ('versionstring', 'reldate', 'current', )

admin.site.register(Version, VersionAdmin)
admin.site.register(OrganisationType)
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(ImportedRSSFeed)
admin.site.register(ImportedRSSItem)

