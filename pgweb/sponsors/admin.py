from django.contrib import admin
from .models import Sponsor, SponsorType, Server


class SponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'sponsortype', 'country']
    list_filter = ['sponsortype']
    search_fields = ['name']


admin.site.register(SponsorType)
admin.site.register(Sponsor, SponsorAdmin)
admin.site.register(Server)
