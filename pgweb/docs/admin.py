from django.contrib import admin

from .models import DocPageAlias, DocPageRedirect

admin.site.register(DocPageAlias)
admin.site.register(DocPageRedirect)
