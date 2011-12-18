from django.contrib import admin
from django import forms

import base64

from models import *

class CommunityAuthSiteAdminForm(forms.ModelForm):
	class Meta:
		model = CommunityAuthSite

	def clean_cryptkey(self):
		x = None
		try:
			x = base64.b64decode(self.cleaned_data['cryptkey'])
		except TypeError, e:
			raise forms.ValidationError("Crypto key must be base64 encoded")

		if (len(x) != 16 and len(x) != 24 and len(x) != 32):
			raise forms.ValidationError("Crypto key must be 16, 24 or 32 bytes before being base64-encoded")
		return self.cleaned_data['cryptkey']

class CommunityAuthSiteAdmin(admin.ModelAdmin):
	form = CommunityAuthSiteAdminForm

		
admin.site.register(CommunityAuthSite, CommunityAuthSiteAdmin)
