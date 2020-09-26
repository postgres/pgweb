from django import forms

from pgweb.core.models import Organisation
from .models import ProfessionalService


class ProfessionalServiceForm(forms.ModelForm):
    form_intro = 'Before submitting an entry, please read the <a href="/about/policies/services-and-hosting/">current policy</a> for Professional Services and Hosting'

    def __init__(self, *args, **kwargs):
        super(ProfessionalServiceForm, self).__init__(*args, **kwargs)

    def filter_by_user(self, user):
        self.fields['org'].queryset = Organisation.objects.filter(managers=user, approved=True)

    class Meta:
        model = ProfessionalService
        exclude = ('submitter', 'approved', )
