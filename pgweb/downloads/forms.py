from django import forms

from pgweb.core.models import Organisation
from models import Product

class ProductForm(forms.ModelForm):
	form_intro = """Note that in order to register a new product, you must first register an organisation.
If you have not done so, use <a href="/account/organisations/new/">this form</a>."""
	def __init__(self, *args, **kwargs):
		super(ProductForm, self).__init__(*args, **kwargs)
	def filter_by_user(self, user):
		print "Filter to user %s" % user
		self.fields['publisher'].queryset = Organisation.objects.filter(submitter=user)
	class Meta:
		model = Product
		exclude = ('lastconfirmed', 'approved', )

