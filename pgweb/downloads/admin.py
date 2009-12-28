from django.contrib import admin
from util.admin import register_markdown, MarkdownPreviewAdmin
from models import *

class ProductAdmin(MarkdownPreviewAdmin):
	list_display = ('name', 'publisher', 'approved', 'lastconfirmed',)
	list_filter = ('approved',)
	search_fields = ('name', 'description', )
	ordering = ('name', )

admin.site.register(Category)
admin.site.register(LicenceType)
admin.site.register(Product, ProductAdmin)

