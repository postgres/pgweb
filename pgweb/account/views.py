from django.contrib.auth.models import User
import django.contrib.auth.views as authviews
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext

from pgweb.news.models import NewsArticle
from pgweb.events.models import Event
from pgweb.core.models import Organisation
from pgweb.downloads.models import Product

@ssl_required
@login_required
def home(request):
	myarticles = NewsArticle.objects.filter(org__managers=request.user, approved=False)
	myevents = Event.objects.filter(org__managers=request.user, approved=False)
	myorgs = Organisation.objects.filter(managers=request.user, approved=False)
	myproducts = Product.objects.filter(publisher__managers=request.user, approved=False)
	return render_to_response('account/index.html', {
		'newsarticles': myarticles,
		'events': myevents,
		'organisations': myorgs,
		'products': myproducts,
	}, NavContext(request, 'account'))

objtypes = {
	'news': {
		'title': 'News articles',
		'objects': lambda u: NewsArticle.objects.filter(org__managers=u),
	},
	'events': {
		'title': 'Events',
		'objects': lambda u: Event.objects.filter(org__managers=u),
    },
	'products': {
		'title': 'Products',
		'objects': lambda u: Product.objects.filter(publisher__managers=u),
	},
	'organisations': {
		'title': 'Organisations',
		'objects': lambda u: Organisation.objects.filter(managers=u),
	},
}

@ssl_required
@login_required
def listobjects(request, objtype):
	if not objtypes.has_key(objtype):
		raise Http404("Object type not found")
	o = objtypes[objtype]

	return render_to_response('account/objectlist.html', {
	    'objects': o['objects'](request.user),
		'title': o['title'],
		'suburl': objtype,
	}, NavContext(request, 'account'))

@ssl_required
def login(request):
	return authviews.login(request, template_name='account/login.html')

@ssl_required
def logout(request):
	return authviews.logout_then_login(request, login_url='/')
