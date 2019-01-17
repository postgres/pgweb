from django import forms
from django.db.models import Q

from pgweb.core.models import Version


class _version_choices():
    def __iter__(self):
        yield ('-1', '** Select version')
        q = Q(supported=True) | Q(testing__gt=0)
        for v in Version.objects.filter(q):
            for minor in range(v.latestminor, -1, -1):
                if not v.testing or minor > 0:
                    # For beta/rc versions, there is no beta0, so exclude it
                    s = v.buildversionstring(minor)
                    yield (s, s)
        yield ('Unsupported/Unknown', 'Unsupported/Unknown')


class SubmitBugForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=100, required=True)
    pgversion = forms.CharField(max_length=20, required=True,
                                label="PostgreSQL version",
                                widget=forms.Select(choices=_version_choices()))
    os = forms.CharField(max_length=50, required=True,
                         label="Operating system")
    shortdesc = forms.CharField(max_length=100, required=True,
                                label="Short description")
    details = forms.CharField(required=True, widget=forms.Textarea)

    def clean_pgversion(self):
        if self.cleaned_data.get('pgversion') == '-1':
            raise forms.ValidationError('You must select a version')
        return self.cleaned_data.get('pgversion')
