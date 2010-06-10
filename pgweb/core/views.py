from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db import connection

from datetime import date

from pgweb.util.decorators import ssl_required, cache
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form

# models needed for the pieces on the frontpage
from news.models import NewsArticle
from events.models import Event
from quotes.models import Quote
from models import Version, ImportedRSSFeed, ImportedRSSItem

# models needed for the pieces on the community page
from survey.models import Survey

# models and forms needed for core objects
from models import Organisation
from forms import OrganisationForm

# models needed to generate unapproved list
from docs.models import DocComment
from downloads.models import Product
from profserv.models import ProfessionalService

# Front page view
@cache(minutes=10)
def home(request):
	news = NewsArticle.objects.filter(approved=True)[:5]
	events = Event.objects.select_related('country').filter(approved=True, training=False, enddate__gt=date.today).order_by('enddate', 'startdate')[:3]
	quote = Quote.objects.filter(approved=True).order_by('?')[0]
	versions = Version.objects.all()
	planet = ImportedRSSItem.objects.filter(feed__internalname="planet").order_by("-posttime")[:5]

	traininginfo = Event.objects.filter(approved=True, training=True).extra(where=("startdate <= (CURRENT_DATE + '6 Months'::interval) AND enddate >= CURRENT_DATE",)).aggregate(Count('id'), Count('country', distinct=True))
	# can't figure out how to make django do this
	curs = connection.cursor()
	curs.execute("SELECT * FROM (SELECT DISTINCT(core_organisation.name) FROM events_event INNER JOIN core_organisation ON org_id=core_organisation.id WHERE startdate <= (CURRENT_DATE + '6 Months'::interval) AND enddate >= CURRENT_DATE AND events_event.approved AND training AND org_id IS NOT NULL) x ORDER BY random() LIMIT 3")
	trainingcompanies = [r[0] for r in curs.fetchall()]

	return render_to_response('index.html', {
		'title': 'The world\'s most advanced open source database',
		'news': news,
		'events': events,
		'traininginfo': traininginfo,
		'trainingcompanies': trainingcompanies,
		'quote': quote,
		'versions': versions,
		'planet': planet,
	})

# Community main page (contains surveys and potentially more)
def community(request):
	s = Survey.objects.filter(current=True)
	try:
		s = s[0]
	except:
		s = None
	planet = ImportedRSSItem.objects.filter(feed__internalname="planet").order_by("-posttime")[:7]
	return render_to_response('core/community.html', {
		'survey': s,
		'planet': planet,
	}, NavContext(request, 'community'))

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

# Edit-forms for core objects
@ssl_required
@login_required
def organisationform(request, itemid):
	return simple_form(Organisation, itemid, request, OrganisationForm, fixedfields={
			'managers': (request.user, ),
			})


# Pending moderation requests (this is part of the /admin/ interface :O)
def _generate_unapproved(objects):
	if not len(objects): return None
	return { 'name': objects[0]._meta.verbose_name_plural, 'entries':
			 [{'url': '/admin/%s/%s/%s/' % (x._meta.app_label, x._meta.module_name, x.pk), 'title': unicode(x)} for x in objects]
			 }


@login_required
def admin_pending(request):
	n = NewsArticle.objects.filter(approved=False)
	app_list = [
		_generate_unapproved(NewsArticle.objects.filter(approved=False)),
		_generate_unapproved(Event.objects.filter(approved=False)),
		_generate_unapproved(Organisation.objects.filter(approved=False)),
		_generate_unapproved(DocComment.objects.filter(approved=False)),
		_generate_unapproved(Product.objects.filter(approved=False)),
		_generate_unapproved(ProfessionalService.objects.filter(approved=False)),
		_generate_unapproved(Quote.objects.filter(approved=False)),
		]

	return render_to_response('core/admin_pending.html', {
			'app_list': [x for x in app_list if x],
			})
