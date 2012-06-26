from django.contrib import admin

from util.admin import PgwebAdmin
from models import *

class EventAdmin(PgwebAdmin):
	list_display = ('title', 'org', 'startdate', 'training', 'approved',)
	list_filter = ('approved','training',)
	search_fields = ('summary', 'details', 'title', )

admin.site.register(Event, EventAdmin)
