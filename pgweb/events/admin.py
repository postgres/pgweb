from django.contrib import admin

from util.admin import PgwebAdmin
from models import *

def approve_event(modeladmin, request, queryset):
	# We need to do this in a loop even though it's less efficient,
	# since using queryset.update() will not send the moderation messages.
	for e in queryset:
		e.approved = True
		e.save()
approve_event.short_description = 'Approve event'

class EventAdmin(PgwebAdmin):
	list_display = ('title', 'org', 'startdate', 'training', 'approved',)
	list_filter = ('approved','training',)
	search_fields = ('summary', 'details', 'title', )
	actions = [approve_event, ]

admin.site.register(Event, EventAdmin)
