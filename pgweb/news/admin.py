from django.contrib import admin

from util.admin import MarkdownPreviewAdmin
from models import *

class NewsArticleAdmin(MarkdownPreviewAdmin):
	list_display = ('title', 'org', 'date', 'approved', )
	list_filter = ('approved', )
	search_fields = ('content', 'title', )

admin.site.register(NewsArticle, NewsArticleAdmin)
