from django import forms

from pgweb.core.models import Organisation
from models import ProfessionalService

class ProfessionalServiceForm(forms.ModelForm):
	form_intro = """Note that in order to register a new professional service, you must first register an organisation.
If you have not done so, use <a href="/account/organisations/new/">this form</a>."""
	def __init__(self, *args, **kwargs):
		super(ProfessionalServiceForm, self).__init__(*args, **kwargs)
	def filter_by_user(self, user):
		self.fields['org'].queryset = Organisation.objects.filter(managers=user, approved=True)
	class Meta:
		model = ProfessionalService
		exclude = ('submitter', 'approved', )

