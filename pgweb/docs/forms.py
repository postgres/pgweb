from django import forms

class DocCommentForm(forms.Form):
	name = forms.CharField(max_length=100, required=True)
	email = forms.EmailField(max_length=100, required=True)
	shortdesc = forms.CharField(max_length=100, required=True,
								label="Short description")
	details = forms.CharField(required=True, widget=forms.Textarea)
