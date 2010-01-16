from django.contrib import admin
from models import *

class DocCommentAdmin(admin.ModelAdmin):
	list_display = ('file', 'version', 'posted_at', 'approved', )

admin.site.register(DocComment, DocCommentAdmin)
