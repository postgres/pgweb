from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist, loader, Context

from pgweb.util.contexts import NavContext

# models needed for the pieces on the frontpage
from news.models import NewsArticle
from events.models import Event
from quotes.models import Quote
from models import Version

# Front page view
def home(request):
	news = NewsArticle.objects.filter(approved=True)[:3]
	events = Event.objects.select_related('country').filter(approved=True).filter(training=False)[:3]
	quote = Quote.objects.filter(approved=True).order_by('?')[0]
	versions = Version.objects.all()

	return render_to_response('index.html', {
		'title': 'The world\'s most advanced open source database',
		'news': news,
		'events': events,
		'quote': quote,
		'versions': versions,
	})


# Generic fallback view for static pages
def fallback(request, url):
	if url.find('..') > -1:
		raise Http404('Page not found.')

	try:
		t = loader.get_template('pages/%s.html' % url)
	except TemplateDoesNotExist, e:
		raise Http404('Page not found.')
		
	# Guestimate the nav section by looking at the URL and taking the first
	# piece of it.
	try:
		navsect = url.split('/',2)[0]
	except:
		navsect = ''
	return HttpResponse(t.render(NavContext(request, navsect)))

