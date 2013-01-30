from django.contrib import admin
from models import *

def approve_doccomment(modeladmin, request, queryset):
	# We need to do this in a loop even though it's less efficient,
	# since using queryset.update() will not send the moderation messages.
	for e in queryset:
		e.approved = True
		e.save()
approve_doccomment.short_description = 'Approve comment'

class DocCommentAdmin(admin.ModelAdmin):
	list_display = ('file', 'version', 'posted_at', 'approved', )
	actions = [approve_doccomment, ]

admin.site.register(DocComment, DocCommentAdmin)
