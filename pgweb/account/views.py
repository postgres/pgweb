from django.contrib.auth.models import User
import django.contrib.auth.views as authviews
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext

from pgweb.news.models import NewsArticle
from pgweb.events.models import Event

@ssl_required
@login_required
def home(request):
	myarticles = NewsArticle.objects.filter(submitter=request.user)
	myevents = Event.objects.filter(submitter=request.user)
	return render_to_response('account/index.html', {
		'newsarticles': myarticles,
		'events': myevents,
	}, NavContext(request, 'account'))

@ssl_required
def login(request):
	return authviews.login(request, template_name='account/login.html')

@ssl_required
def logout(request):
	return authviews.logout_then_login(request, login_url='/')
