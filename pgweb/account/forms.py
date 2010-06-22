from django import forms

from django.contrib.auth.models import User

class SignupForm(forms.Form):
	username = forms.CharField(max_length=30)
	first_name = forms.CharField(max_length=30)
	last_name = forms.CharField(max_length=30)
	email = forms.EmailField()
	email2 = forms.EmailField()

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
