from django import forms
from django.forms import ValidationError
from django.conf import settings

from .models import Organisation, OrganisationEmail
from django.contrib.auth.models import User

from pgweb.util.middleware import get_current_user
from pgweb.util.moderation import ModerationState
from pgweb.mailqueue.util import send_simple_mail
from pgweb.util.misc import send_template_mail, generate_random_token


class OrganisationForm(forms.ModelForm):
    new_form_intro = """<em>Note!</em> An organisation record is only needed to post news, events,
products or professional services. In particular, it is <em>not</em> necessary to register an
organisation in order to ask questions or otherwise participate on the PostgreSQL mailing lists, file a bug
report, or otherwise interact with the community."""

    remove_email = forms.ModelMultipleChoiceField(required=False, queryset=None, label="Current email addresses", help_text="Select one or more email addresses to remove")
    add_email = forms.EmailField(required=False, help_text="Enter an email address to add")
    remove_manager = forms.ModelMultipleChoiceField(required=False, queryset=None, label="Current manager(s)", help_text="Select one or more managers to remove")
    add_manager = forms.EmailField(required=False, help_text="Enter an email address of an existing account to add as manager")

    fieldsets = [
        {
            'id': 'general',
            'legend': 'General',
            'description': '',
            'fields': ['name', 'address', 'url', 'orgtype', ],
        },
        {
            'id': 'managers',
            'legend': 'Managers',
            'description': 'Managers are the accounts that can use and modify this organisation. To add a manager they must have an existing account.',
            'fields': ['remove_manager', 'add_manager'],
        },
        {
            'id': 'emails',
            'legend': 'E-mail addresses',
            'description': 'E-mail addresses registered here can be used to post news. If no news will be posted, there is no need to register one or more email addresses.',
            'fields': ['remove_email', 'add_email'],
        },
    ]

    class Meta:
        model = Organisation
        exclude = ('lastconfirmed', 'approved', 'managers', 'mailtemplate', 'fromnameoverride')

    def __init__(self, *args, **kwargs):
        super(OrganisationForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['remove_manager'].queryset = self.instance.managers.all()
        else:
            del self.fields['remove_manager']
            del self.fields['add_manager']
            # remove the managers fieldset
            self.fieldsets = [fs for fs in self.fieldsets if fs['id'] != 'managers']

        if self.instance and self.instance.pk and self.instance.is_approved:
            # Only allow adding/removing emails on orgs that are actually approved
            self.fields['remove_email'].queryset = OrganisationEmail.objects.filter(org=self.instance)
        else:
            del self.fields['remove_email']
            del self.fields['add_email']
            # remove the emails fieldset
            self.fieldsets = [fs for fs in self.fieldsets if fs['id'] != 'emails']

    def clean_add_email(self):
        if self.cleaned_data['add_email']:
            if OrganisationEmail.objects.filter(org=self.instance, address=self.cleaned_data['add_email'].lower()).exists():
                raise ValidationError("This email is already registered for your organisation.")
        return self.cleaned_data['add_email']

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

    def clean_remove_email(self):
        if self.cleaned_data['remove_email']:
            for e in self.cleaned_data['remove_email']:
                if e.newsarticle_set.exists():
                    raise ValidationError("Cannot remove an email address that has been used to post news articles. Please contact webmaster@postgresql.org to have this removed.")
        return self.cleaned_data['remove_email']

    def save(self, commit=True):
        model = super(OrganisationForm, self).save(commit=False)

        ops = []
        if self.cleaned_data.get('add_email', None):
            # Create the email record
            e = OrganisationEmail(org=model, address=self.cleaned_data['add_email'].lower(), token=generate_random_token())
            e.save()

            # Send email for confirmation
            send_template_mail(
                settings.NOTIFICATION_FROM,
                e.address,
                "Email address added to postgresql.org organisation",
                'core/org_add_email.txt',
                {
                    'org': model,
                    'email': e,
                },
            )
            ops.append('Added email {}, confirmation request sent'.format(e.address))
        if self.cleaned_data.get('remove_email', None):
            for e in self.cleaned_data['remove_email']:
                ops.append('Removed email {}'.format(e.address))
                e.delete()

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
                "{0} modified {1}".format(get_current_user().username, model),
                "The following changes were made to {}:\n\n{}".format(model, "\n".join(ops))
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
        self.user = kwargs.pop('user')
        self.obj = kwargs.pop('obj')
        self.twostate = hasattr(self.obj, 'approved')

        super().__init__(*args, **kwargs)
        if self.twostate:
            self.fields['modstate'].choices = [(k, v) for k, v in self.fields['modstate'].choices if int(k) != 1]
        if self.obj.twomoderators:
            if self.obj.firstmoderator:
                self.fields['modstate'].help_text = 'This object requires approval from two moderators. It has already been approved by {}.'.format(self.obj.firstmoderator)
            else:
                self.fields['modstate'].help_text = 'This object requires approval from two moderators.'

    def clean_modstate(self):
        state = int(self.cleaned_data['modstate'])
        if state == ModerationState.APPROVED and self.obj.twomoderators and self.obj.firstmoderator == self.user:
            raise ValidationError("You already moderated this object, waiting for a *different* moderator")
        return state

    def clean(self):
        cleaned_data = super().clean()

        note = cleaned_data['modnote']

        if note and int(cleaned_data['modstate']) == ModerationState.APPROVED and self.obj.twomoderators and not self.obj.firstmoderator:
            self.add_error('modnote', ("Moderation notices cannot be sent on first-moderator approvals for objects that require two moderators."))

        return cleaned_data


class AdminResetPasswordForm(forms.Form):
    confirm = forms.BooleanField(required=True, label="Confirm that you want to reset this password")
