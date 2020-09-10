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

        if hasattr(self.model, 'markdown_fields'):
            if db_field.name in self.model.markdown_fields:
                fld.widget.attrs['class'] = fld.widget.attrs['class'] + ' markdown_preview'
        return fld

    # Remove the builtin delete_selected action, so it doesn't
    # conflict with the custom one.
    def get_actions(self, request):
        actions = super(PgwebAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    # Define a custom delete_selected action. This is required because the
    # default one uses the delete functionality in QuerySet, which bypasses
    # the delete() operation on the model, and thus won't send out our
    # notifications. Manually calling delete() on each one will be slightly
    # slower, but will send proper notifications - and it's not like this
    # is something that happens often enough that we care about performance.
    def custom_delete_selected(self, request, queryset):
        for x in queryset:
            x.delete()
    custom_delete_selected.short_description = "Delete selected items"
    actions = ['custom_delete_selected']


def register_pgwebadmin(model):
    admin.site.register(model, PgwebAdmin)
