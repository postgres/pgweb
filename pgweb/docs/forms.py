from django import forms

class DocCommentForm(forms.Form):
	name = forms.CharField(max_length=100, required=True)
	email = forms.EmailField(max_length=100, required=True, label="Your email")
	shortdesc = forms.CharField(max_length=100, required=True,
								label="Email subject")
	details = forms.CharField(required=True, widget=forms.Textarea,
							  label="Email body")
