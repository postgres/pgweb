from django.contrib import admin
from models import *

class QuoteAdmin(admin.ModelAdmin):
	list_display = ('quote', 'who', 'org', )

admin.site.register(Quote, QuoteAdmin)
