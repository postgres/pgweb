from django import forms
from django.forms import ValidationError
from django.conf import settings

from .models import Organisation
from django.contrib.auth.models import User

from pgweb.util.middleware import get_current_user
from pgweb.util.moderation import ModerationState
from pgweb.mailqueue.util import send_simple_mail


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
        ops = []
        if 'add_manager' in self.cleaned_data and self.cleaned_data['add_manager']:
            u = User.objects.get(email=self.cleaned_data['add_manager'].lower())
            model.managers.add(u)
            ops.append('Added manager {}'.format(u.username))
        if 'remove_manager' in self.cleaned_data and self.cleaned_data['remove_manager']:
            for toremove in self.cleaned_data['remove_manager']:
                model.managers.remove(toremove)
                ops.append('Removed manager {}'.format(toremove.username))

        if ops:
            send_simple_mail(
                settings.NOTIFICATION_FROM,
                settings.NOTIFICATION_EMAIL,
                "{0} modified managers of {1}".format(get_current_user().username, model),
                "The following changes were made to managers:\n\n{0}".format("\n".join(ops))
            )
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


class ModerationForm(forms.Form):
    modnote = forms.CharField(label='Moderation notice', widget=forms.Textarea, required=False,
                              help_text="This note will be sent to the creator of the object regardless of if the moderation state has changed.")
    oldmodstate = forms.CharField(label='Current moderation state', disabled=True)
    modstate = forms.ChoiceField(label='New moderation status', choices=ModerationState.CHOICES + (
        (ModerationState.REJECTED, 'Reject and delete'),
    ))

    def __init__(self, *args, **kwargs):
        self.twostate = kwargs.pop('twostate')
        super().__init__(*args, **kwargs)
        if self.twostate:
            self.fields['modstate'].choices = [(k, v) for k, v in self.fields['modstate'].choices if int(k) != 1]
