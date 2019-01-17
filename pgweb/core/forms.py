from django import forms
from django.forms import ValidationError

from models import Organisation
from django.contrib.auth.models import User


class OrganisationForm(forms.ModelForm):
    remove_manager = forms.ModelMultipleChoiceField(required=False, queryset=None, label="Current manager(s)", help_text="Select one or more managers to remove")
    add_manager = forms.EmailField(required=False)

    class Meta:
        model = Organisation
        exclude = ('lastconfirmed', 'approved', 'managers', )

    def __init__(self, *args, **kwargs):
        super(OrganisationForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['remove_manager'].queryset = self.instance.managers.all()
        else:
            del self.fields['remove_manager']
            del self.fields['add_manager']

    def clean_add_manager(self):
        if self.cleaned_data['add_manager']:
            # Something was added as manager - let's make sure the user exists
            try:
                User.objects.get(email=self.cleaned_data['add_manager'].lower())
            except User.DoesNotExist:
                raise ValidationError("User with email %s not found" % self.cleaned_data['add_manager'])

        return self.cleaned_data['add_manager']

    def clean_remove_manager(self):
        if self.cleaned_data['remove_manager']:
            removecount = 0
            for toremove in self.cleaned_data['remove_manager']:
                if toremove in self.instance.managers.all():
                    removecount += 1

            if len(self.instance.managers.all()) - removecount <= 0:
                raise ValidationError("Cannot remove all managers from an organsation!")
        return self.cleaned_data['remove_manager']

    def save(self, commit=True):
        model = super(OrganisationForm, self).save(commit=False)
        if self.cleaned_data.has_key('add_manager') and self.cleaned_data['add_manager']:
            model.managers.add(User.objects.get(email=self.cleaned_data['add_manager'].lower()))
        if self.cleaned_data.has_key('remove_manager') and self.cleaned_data['remove_manager']:
            for toremove in self.cleaned_data['remove_manager']:
                model.managers.remove(toremove)

        return model

    def apply_submitter(self, model, User):
        model.managers.add(User)


class MergeOrgsForm(forms.Form):
    merge_into = forms.ModelChoiceField(queryset=Organisation.objects.all())
    merge_from = forms.ModelChoiceField(queryset=Organisation.objects.all())

    def clean(self):
        if self.cleaned_data['merge_into'] == self.cleaned_data['merge_from']:
            raise ValidationError("The two organisations selected must be different!")
        return self.cleaned_data
