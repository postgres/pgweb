from django.contrib import admin
from django import forms
from django.db import connection
from django.http import HttpResponseRedirect, HttpResponse

from pgweb.core.models import *

class OrganisationAdmin(admin.ModelAdmin):
	list_display = ('name', 'approved', 'lastconfirmed',)
	list_filter = ('approved',)
	ordering = ('name', )


admin.site.register(Version)
admin.site.register(OrganisationType)
admin.site.register(Organisation, OrganisationAdmin)

