from django import forms
from django.contrib.auth.forms import AuthenticationForm

import re

from django.contrib.auth.models import User
from pgweb.core.models import UserProfile
from pgweb.contributors.models import Contributor

from recaptcha import ReCaptchaField

import logging
log = logging.getLogger(__name__)

def _clean_username(username):
	username = username.lower()

	if not re.match('^[a-z0-9\.-]+$', username):
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
		except ValueError, e:
			if e.message.startswith('Unknown password hashing algorithm'):
				# This is *probably* a user trying to log in with an account that has not
				# been set up properly yet. It could be an actually unsupported hashing
				# algorithm, but we'll deal with that when we get there.
				self._errors["__all__"] = self.error_class(["This account appears not to be properly initialized. Make sure you complete the signup process with the instructions in the email received before trying to use the account."])
				log.warning("User {0} tried to log in with invalid hash, probably because signup was completed.".format(self.cleaned_data['username']))
				return self.cleaned_data
			raise e


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
		if not self.cleaned_data.has_key('email'):
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

		try:
			User.objects.get(email=email)
		except User.DoesNotExist:
			return email
		raise forms.ValidationError("A user with this email address is already registered")

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

class UserProfileForm(forms.ModelForm):
	class Meta:
		model = UserProfile
		exclude = ('user',)

class UserForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(UserForm, self).__init__(*args, **kwargs)
		self.fields['first_name'].required = True
		self.fields['last_name'].required = True
	class Meta:
		model = User
		fields = ('first_name', 'last_name', )

class ContributorForm(forms.ModelForm):
	class Meta:
		model = Contributor
		exclude = ('ctype', 'lastname', 'firstname', 'user', )

class ChangeEmailForm(forms.Form):
	email = forms.EmailField()
	email2 = forms.EmailField(label="Repeat email")

	def __init__(self, user, *args, **kwargs):
		super(ChangeEmailForm, self).__init__(*args, **kwargs)
		self.user = user

	def clean_email(self):
		email = self.cleaned_data['email']

		if email == self.user.email:
			raise forms.ValidationError("This is your existing email address!")

		if User.objects.filter(email=email).exists():
			raise forms.ValidationError("A user with this email address is already registered")

		return email

	def clean_email2(self):
		# If the primary email checker had an exception, the data will be gone
		# from the cleaned_data structure
		if not self.cleaned_data.has_key('email'):
			return self.cleaned_data['email2']
		email1 = self.cleaned_data['email'].lower()
		email2 = self.cleaned_data['email2'].lower()

		if email1 != email2:
			raise forms.ValidationError("Email addresses don't match")
		return email2
