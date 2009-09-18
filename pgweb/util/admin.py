from django.contrib import admin

class MarkdownPreviewAdmin(admin.ModelAdmin):
	"""
	ModelAdmin wrapper that will enable preview fields for all markdown capable
	textfields in the model (specified by including them in a class variable
	named markdown_capable that is a tuple of field names)
	"""

	change_form_template = 'admin/change_form_markdown.html'

	def formfield_for_dbfield(self, db_field, **kwargs):
		fld = admin.ModelAdmin.formfield_for_dbfield(self, db_field, **kwargs)

		if db_field.name in self.model.markdown_fields:
			fld.widget.attrs['class'] = fld.widget.attrs['class'] + ' markdown_preview'
		return fld

def register_markdown(model):
	admin.site.register(model, MarkdownPreviewAdmin)

