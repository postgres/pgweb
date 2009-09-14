from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from pgweb.util.contexts import NavContext

from pgweb.news.models import NewsArticle
from pgweb.events.models import Event

@login_required
def home(request):
	myarticles = NewsArticle.objects.filter(submitter=request.user)
	myevents = Event.objects.filter(submitter=request.user)
	return render_to_response('account/index.html', {
		'newsarticles': myarticles,
		'events': myevents,
	}, NavContext(request, 'account'))

