from django.contrib import admin

class PgwebAdmin(admin.ModelAdmin):
	"""
	ModelAdmin wrapper that will enable a few pg specific things:
	* Markdown preview for markdown capable textfields (specified by
	  including them in a class variable named markdown_capable that is a tuple
	  of field names)
	"""

	change_form_template = 'admin/change_form_pgweb.html'

	def formfield_for_dbfield(self, db_field, **kwargs):
		fld = admin.ModelAdmin.formfield_for_dbfield(self, db_field, **kwargs)

		if db_field.name in self.model.markdown_fields:
			fld.widget.attrs['class'] = fld.widget.attrs['class'] + ' markdown_preview'
		return fld

def register_pgwebadmin(model):
	admin.site.register(model, PgwebAdmin)

