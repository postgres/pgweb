from django.contrib import admin
from util.admin import register_markdown, MarkdownPreviewAdmin
from models import *

class MirrorAdmin(admin.ModelAdmin):
	list_display = ('__unicode__', 'country_name', 'country_code', 'mirror_index', 'mirror_last_rsync', 'host_sponsor', )
	list_filter = ('country_name', 'mirror_active', )
	search_fields = ('country_name', 'host_sponsor', 'host_notes', )
	ordering = ('country_code', )

class ProductAdmin(MarkdownPreviewAdmin):
	list_display = ('name', 'publisher', 'approved', 'lastconfirmed',)
	list_filter = ('approved',)
	search_fields = ('name', 'description', )
	ordering = ('name', )

def duplicate_stackbuilderapp(modeladmin, request, queryset):
	# Duplicate each individual selected object, but turn off
	# the active flag if it's on.
	for o in queryset:
		o.id = None # Triggers creation of a new object
		o.active = False
		o.textid = o.textid + "_new"
		o.save()

duplicate_stackbuilderapp.short_description = "Duplicate application"

class StackBuilderAppAdmin(admin.ModelAdmin):
	list_display = ('textid', 'active', 'name', 'platform', 'version', )
	filter_horizontal = ('dependencies', )
	actions = [duplicate_stackbuilderapp, ]


admin.site.register(Mirror, MirrorAdmin)
admin.site.register(Category)
admin.site.register(LicenceType)
admin.site.register(Product, ProductAdmin)
admin.site.register(StackBuilderApp, StackBuilderAppAdmin)
