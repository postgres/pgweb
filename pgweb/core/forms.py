from django import forms
from django.forms import ValidationError

from models import Organisation

class OrganisationForm(forms.ModelForm):
	class Meta:
		model = Organisation
		exclude = ('lastconfirmed', 'approved', 'managers', )

class MergeOrgsForm(forms.Form):
	merge_into = forms.ModelChoiceField(queryset=Organisation.objects.all())
	merge_from = forms.ModelChoiceField(queryset=Organisation.objects.all())

	def clean(self):
		if self.cleaned_data['merge_into'] == self.cleaned_data['merge_from']:
			raise ValidationError("The two organisations selected must be different!")
		return self.cleaned_data
