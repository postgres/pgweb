from django.contrib import admin

from util.admin import MarkdownPreviewAdmin
from models import *

class EventAdmin(MarkdownPreviewAdmin):
	list_display = ('title', 'org', 'startdate', 'training', 'approved',)
	list_filter = ('approved','training',)
	search_fields = ('org', 'summary', 'details', 'title', )

admin.site.register(Event, EventAdmin)
