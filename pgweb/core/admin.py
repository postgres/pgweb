from django.contrib import admin
from django import forms
from django.db import connection
from django.http import HttpResponseRedirect, HttpResponse

from pgweb.core.models import *

admin.site.register(Version)
