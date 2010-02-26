from django import forms

from models import Organisation

class OrganisationForm(forms.ModelForm):
	class Meta:
		model = Organisation
		exclude = ('lastconfirmed', 'approved', 'managers', )

