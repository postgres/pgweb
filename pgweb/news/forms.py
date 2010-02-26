from django import forms

from pgweb.core.models import Organisation
from models import NewsArticle

class NewsArticleForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(NewsArticleForm, self).__init__(*args, **kwargs)
	def filter_by_user(self, user):
		self.fields['org'].queryset = Organisation.objects.filter(managers=user, approved=True)
	class Meta:
		model = NewsArticle
		exclude = ('submitter', 'approved', )

