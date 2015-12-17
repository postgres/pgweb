from django import forms

import re

from django.contrib.auth.models import User
from pgweb.core.models import UserProfile
from pgweb.contributors.models import Contributor

from recaptcha import ReCaptchaField

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
		username = self.cleaned_data['username'].lower()

		raise forms.ValidationError("Signups are temporarily disabled")

		if not re.match('^[a-z0-9_@\.-]+$', username):
			raise forms.ValidationError("Invalid character in user name. Only a-z, 0-9, _, @, . and - allowed.")
		try:
			User.objects.get(username=username)
		except User.DoesNotExist:
			return username
		raise forms.ValidationError("This username is already in use")

	def clean_email(self):
		email = self.cleaned_data['email'].lower()

		try:
			User.objects.get(email=email)
		except User.DoesNotExist:
			return email
		raise forms.ValidationError("A user with this email address is already registered")

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
