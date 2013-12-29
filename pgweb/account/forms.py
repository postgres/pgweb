from django import forms

import re

from django.contrib.auth.models import User
from pgweb.core.models import UserProfile
from pgweb.contributors.models import Contributor

class SignupForm(forms.Form):
	username = forms.CharField(max_length=30)
	first_name = forms.CharField(max_length=30)
	last_name = forms.CharField(max_length=30)
	email = forms.EmailField()
	email2 = forms.EmailField(label="Repeat email")

	def clean_email2(self):
		# If the primary email checker had an exception, the data will be gone
		# from the cleaned_data structure
		if not self.cleaned_data.has_key('email'):
			return self.cleaned_data['email2']
		email1 = self.cleaned_data['email']
		email2 = self.cleaned_data['email2']

		if email1 != email2:
			raise forms.ValidationError("Email addresses don't match")
		return email2

	def clean_username(self):
		username = self.cleaned_data['username'].lower()

		if not re.match('^[a-z0-9_@\.-]+$', username):
			raise forms.ValidationError("Invalid character in user name. Only a-z, 0-9, _, @, . and - allowed.")
		try:
			u = User.objects.get(username=username)
		except User.DoesNotExist:
			return username
		raise forms.ValidationError("This username is already in use")

	def clean_email(self):
		email = self.cleaned_data['email']

		try:
			u = User.objects.get(email=email)
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
		exclude = ('ctype', 'lastname', 'firstname', 'email', 'user', )
