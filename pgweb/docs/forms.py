from django import forms

from models import DocComment

class DocCommentForm(forms.ModelForm):
	class Meta:
		model = DocComment
		exclude = ('submitter', 'approved', 'version', 'file', 'posted_at', )

