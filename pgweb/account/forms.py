from django import forms
from django.contrib.auth.forms import AuthenticationForm

import re

from django.contrib.auth.models import User
from pgweb.core.models import UserProfile
from pgweb.contributors.models import Contributor
from .models import SecondaryEmail

from .recaptcha import ReCaptchaField

import logging
log = logging.getLogger(__name__)


def _clean_username(username):
    username = username.lower()

    if not re.match(r'^[a-z0-9\.-]+$', username):
        # XXX: Note! Should we ever allow @ signs in usernames again, we need to also
        #      update util/auth.py and the code for identifying email addresses.
        raise forms.ValidationError("Invalid character in user name. Only a-z, 0-9, . and - allowed for compatibility with third party software.")
    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        return username
    raise forms.ValidationError("This username is already in use")


# Override some error handling only in the default authentication form
class PgwebAuthenticationForm(AuthenticationForm):
    def clean(self):
        try:
            return super(PgwebAuthenticationForm, self).clean()
        except ValueError as e:
            if e.message.startswith('Unknown password hashing algorithm'):
                # This is *probably* a user trying to log in with an account that has not
                # been set up properly yet. It could be an actually unsupported hashing
                # algorithm, but we'll deal with that when we get there.
                self._errors["__all__"] = self.error_class(["This account appears not to be properly initialized. Make sure you complete the signup process with the instructions in the email received before trying to use the account."])
                log.warning("User {0} tried to log in with invalid hash, probably because signup was completed.".format(self.cleaned_data['username']))
                return self.cleaned_data
            raise e


class CommunityAuthConsentForm(forms.Form):
    consent = forms.BooleanField(help_text='Consent to sharing this data')
    next = forms.CharField(widget=forms.widgets.HiddenInput())

    def __init__(self, orgname, *args, **kwargs):
        self.orgname = orgname
        super(CommunityAuthConsentForm, self).__init__(*args, **kwargs)

        self.fields['consent'].label = 'Consent to sharing data with {0}'.format(self.orgname)


class SignupForm(forms.Form):
    username = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    email2 = forms.EmailField(label="Repeat email")
    captcha = ReCaptchaField()

    def __init__(self, remoteip, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields['captcha'].set_ip(remoteip)

    def clean_email2(self):
        # If the primary email checker had an exception, the data will be gone
        # from the cleaned_data structure
        if 'email' not in self.cleaned_data:
            return self.cleaned_data['email2']
        email1 = self.cleaned_data['email'].lower()
        email2 = self.cleaned_data['email2'].lower()

        if email1 != email2:
            raise forms.ValidationError("Email addresses don't match")
        return email2

    def clean_username(self):
        return _clean_username(self.cleaned_data['username'])

    def clean_email(self):
        email = self.cleaned_data['email'].lower()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address is already registered")

        if SecondaryEmail.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already attached to a different user")

        return email


class SignupOauthForm(forms.Form):
    username = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField()
    captcha = ReCaptchaField()

    def __init__(self, *args, **kwargs):
        super(SignupOauthForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['readonly'] = True
        self.fields['first_name'].widget.attrs['disabled'] = True
        self.fields['last_name'].widget.attrs['readonly'] = True
        self.fields['last_name'].widget.attrs['disabled'] = True
        self.fields['email'].widget.attrs['readonly'] = True
        self.fields['email'].widget.attrs['disabled'] = True

    def clean_username(self):
        return _clean_username(self.cleaned_data['username'])

    def clean_email(self):
        return self.cleaned_data['email'].lower()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user',)


class UserForm(forms.ModelForm):
    primaryemail = forms.ChoiceField(choices=[], required=True, label='Primary email address')

    def __init__(self, can_change_email, secondaryaddresses, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        if can_change_email:
            self.fields['primaryemail'].choices = [(self.instance.email, self.instance.email), ] + [(a.email, a.email) for a in secondaryaddresses if a.confirmed]
            if not secondaryaddresses:
                self.fields['primaryemail'].help_text = "To change the primary email address, first add it as a secondary address below"
        else:
            self.fields['primaryemail'].choices = [(self.instance.email, self.instance.email), ]
            self.fields['primaryemail'].help_text = "You cannot change the primary email of this account since it is connected to an external authentication system"
            self.fields['primaryemail'].widget.attrs['disabled'] = True
            self.fields['primaryemail'].required = False

    class Meta:
        model = User
        fields = ('primaryemail', 'first_name', 'last_name', )


class ContributorForm(forms.ModelForm):
    class Meta:
        model = Contributor
        exclude = ('ctype', 'lastname', 'firstname', 'user', )


class AddEmailForm(forms.Form):
    email1 = forms.EmailField(label="New email", required=False)
    email2 = forms.EmailField(label="Repeat email", required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_email1(self):
        email = self.cleaned_data['email1'].lower()

        if email == self.user.email:
            raise forms.ValidationError("This is your existing email address!")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address is already registered")

        try:
            s = SecondaryEmail.objects.get(email=email)
            if s.user == self.user:
                raise forms.ValidationError("This email address is already connected to your account")
            else:
                raise forms.ValidationError("A user with this email address is already registered")
        except SecondaryEmail.DoesNotExist:
            pass

        return email

    def clean_email2(self):
        # If the primary email checker had an exception, the data will be gone
        # from the cleaned_data structure
        if 'email1' not in self.cleaned_data:
            return self.cleaned_data['email2'].lower()
        email1 = self.cleaned_data['email1'].lower()
        email2 = self.cleaned_data['email2'].lower()

        if email1 != email2:
            raise forms.ValidationError("Email addresses don't match")
        return email2


class PgwebPasswordResetForm(forms.Form):
    email = forms.EmailField()


class ConfirmSubmitForm(forms.Form):
    confirm = forms.BooleanField(required=True, help_text='Confirm')

    def __init__(self, objtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['confirm'].help_text = 'Confirm that you are ready to submit this {}.'.format(objtype)
