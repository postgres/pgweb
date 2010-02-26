from django import forms

from pgweb.core.models import Organisation
from models import Event

class EventForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(EventForm, self).__init__(*args, **kwargs)
	def filter_by_user(self, user):
		self.fields['org'].queryset = Organisation.objects.filter(managers=user, approved=True)
	class Meta:
		model = Event
		exclude = ('submitter', 'approved', )
