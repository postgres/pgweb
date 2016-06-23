from django import forms
from django.contrib import admin

from selectable.forms.widgets import AutoCompleteSelectMultipleWidget

from pgweb.core.models import Version, OrganisationType, Organisation
from pgweb.core.models import ImportedRSSFeed, ImportedRSSItem
from pgweb.core.models import ModerationNotification

from pgweb.core.lookups import UserLookup

class OrganisationAdminForm(forms.ModelForm):
	class Meta:
		model = Organisation
		exclude = ()
		widgets = {
			'managers': AutoCompleteSelectMultipleWidget(lookup_class=UserLookup),
		}

	def __init__(self, *args, **kwargs):
		super(OrganisationAdminForm, self).__init__(*args, **kwargs)
		self.fields['managers'].widget.can_add_related = False
		self.fields['managers'].widget.can_change_related = False
		self.fields['managers'].widget.can_delete_related = False

class OrganisationAdmin(admin.ModelAdmin):
	form = OrganisationAdminForm
	list_display = ('name', 'approved', 'lastconfirmed',)
	list_filter = ('approved',)
	ordering = ('name', )
	search_fields = ('name', )

class VersionAdmin(admin.ModelAdmin):
	list_display = ('versionstring', 'reldate', 'supported', 'current', )

admin.site.register(Version, VersionAdmin)
admin.site.register(OrganisationType)
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(ImportedRSSFeed)
admin.site.register(ImportedRSSItem)
admin.site.register(ModerationNotification)

