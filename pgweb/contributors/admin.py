from django import forms
from django.contrib import admin

from selectable.forms.widgets import AutoCompleteSelectWidget

from pgweb.core.lookups import UserLookup

from models import Contributor, ContributorType

class ContributorAdminForm(forms.ModelForm):
	class Meta:
		model = Contributor
		exclude = ()
		widgets = {
			'user': AutoCompleteSelectWidget(lookup_class=UserLookup),
		}

	def __init__(self, *args, **kwargs):
		super(ContributorAdminForm, self).__init__(*args, **kwargs)
		self.fields['user'].widget.can_add_related = False
		self.fields['user'].widget.can_change_related = False

class ContributorAdmin(admin.ModelAdmin):
	form = ContributorAdminForm

admin.site.register(ContributorType)
admin.site.register(Contributor, ContributorAdmin)
