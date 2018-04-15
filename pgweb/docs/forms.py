from django import forms

class DocCommentForm(forms.Form):
	name = forms.CharField(max_length=100, required=True, label='Your Name')
	email = forms.EmailField(max_length=100, required=True, label='Your Email')
	shortdesc = forms.CharField(max_length=100, required=True, label="Subject")
	details = forms.CharField(required=True, widget=forms.Textarea,
		label="What is your comment?")
