from django.contrib import admin

from pgweb.util.admin import PgwebAdmin
from .models import ProfessionalService


class ProfessionalServiceAdmin(PgwebAdmin):
    list_display = ('__unicode__', 'approved',)
    list_filter = ('approved',)
    search_fields = ('org__name',)


admin.site.register(ProfessionalService, ProfessionalServiceAdmin)
