from django.contrib import admin

from pgweb.util.admin import PgwebAdmin
from .models import PUG


class PUGAdmin(PgwebAdmin):
    list_display = ('title', 'approved', )
    list_filter = ('approved', )
    search_fields = ('title', )


admin.site.register(PUG, PUGAdmin)
