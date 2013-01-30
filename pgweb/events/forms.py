from django import forms

from pgweb.core.models import Organisation
from models import Event

class EventForm(forms.ModelForm):
	toggle_fields = [{
			'name': 'isonline',
			'invert': True,
			'fields': ['city', 'state', 'country',]
			},
					 ]
	def __init__(self, *args, **kwargs):
		super(EventForm, self).__init__(*args, **kwargs)
	def filter_by_user(self, user):
		self.fields['org'].queryset = Organisation.objects.filter(managers=user, approved=True)

	def clean(self):
		cleaned_data = super(EventForm, self).clean()
		if not cleaned_data.get('isonline'):
			# Non online events require city and country
			# (we don't require state, since many countries have no such thing)
			if not cleaned_data.get('city'):
				self._errors['city'] = self.error_class(['City must be specified for non-online events'])
				del cleaned_data['city']
			if not cleaned_data.get('country'):
				self._errors['country'] = self.error_class(['Country must be specified for non-online events'])
				del cleaned_data['country']
		return cleaned_data

	class Meta:
		model = Event
		exclude = ('submitter', 'approved', )
