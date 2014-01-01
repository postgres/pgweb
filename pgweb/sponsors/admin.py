from django.contrib import admin
from models import Sponsor, SponsorType, Server

admin.site.register(SponsorType)
admin.site.register(Sponsor)
admin.site.register(Server)

