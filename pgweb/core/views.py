from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.db import connection, transaction

from datetime import date, datetime
from os import uname
import re
import urllib

from pgweb.util.decorators import ssl_required, cache
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form, PgXmlHelper
from pgweb.util.moderation import get_all_pending_moderations
from pgweb.util.misc import get_client_ip, is_behind_cache, varnish_purge
from pgweb.util.sitestruct import get_all_pages_struct

# models needed for the pieces on the frontpage
from news.models import NewsArticle
from events.models import Event
from quotes.models import Quote
from models import Version, ImportedRSSFeed, ImportedRSSItem

# models needed for the pieces on the community page
from survey.models import Survey

# models and forms needed for core objects
from models import Organisation
from forms import OrganisationForm, MergeOrgsForm

# Front page view
@cache(minutes=10)
def home(request):
	news = NewsArticle.objects.filter(approved=True)[:5]
	events = Event.objects.select_related('country').filter(approved=True, training=False, enddate__gt=date.today).order_by('enddate', 'startdate')[:3]
	try:
		quote = Quote.objects.filter(approved=True).order_by('?')[0]
	except:
		pass # if there is no quote available, just ignore error
	versions = Version.objects.filter(supported=True)
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


re_staticfilenames = re.compile("^[0-9A-Z/_-]+$", re.IGNORECASE)
# Generic fallback view for static pages
def fallback(request, url):
	if url.find('..') > -1:
		raise Http404('Page not found.')

	if not re_staticfilenames.match(url):
		raise Http404('Page not found.')

	try:
		t = loader.get_template('pages/%s.html' % url)
	except TemplateDoesNotExist, e:
		try:
			t = loader.get_template('pages/%s/en.html' % url)
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
	return simple_form(Organisation, itemid, request, OrganisationForm,
					   redirect='/account/edit/organisations/')

# robots.txt
def robots(request):
	if not is_behind_cache(request):
		# If we're not serving this through one of our Varnish caches, we allow *nothing* to be indexed
		return HttpResponse("User-agent: *\nDisallow: /\n", mimetype='text/plain')
	else:
		# Regular website
		return HttpResponse("""User-agent: *
Disallow: /admin/
Disallow: /account/

Sitemap: http://www.postgresql.org/sitemap.xml
""", mimetype='text/plain')


# Sitemap (XML format)
@cache(hours=6)
def sitemap(request):
	resp = HttpResponse(mimetype='text/xml')
	x = PgXmlHelper(resp)
	x.startDocument()
	x.startElement('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})
	pages = 0
	for p in get_all_pages_struct():
		pages+=1
		x.startElement('url', {})
		x.add_xml_element('loc', 'http://www.postgresql.org/%s' % urllib.quote(p[0]))
		if p[1]:
			x.add_xml_element('priority', unicode(p[1]))
		x.endElement('url')
	x.endElement('urlset')
	x.endDocument()
	return resp

# Basic information about the connection
@cache(seconds=30)
def system_information(request):
	return render_to_response('core/system_information.html', {
			'server': uname()[1],
			'behind_cache': is_behind_cache(request),
			'cache_server': is_behind_cache(request) and request.META['REMOTE_ADDR'] or None,
			'client_ip': get_client_ip(request),
	})

# Sync timestamp for automirror. Keep it around for 30 seconds
# Basically just a check that we can access the backend still...
@cache(seconds=30)
def sync_timestamp(request):
	s = datetime.now().strftime("%Y-%m-%d %H:%M:%S\n")
	r = HttpResponse(s,	mimetype='text/plain')
	r['Content-Length'] = len(s)
	return r

# List of all unapproved objects, for the special admin page
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_pending(request):
	return render_to_response('core/admin_pending.html', {
			'app_list': get_all_pending_moderations(),
			})

# Purge objects from varnish, for the admin pages
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_purge(request):
	if request.method == 'POST':
		url = request.POST['url']
		if url == '':
			return HttpResponseRedirect('.')
		varnish_purge(url)
		transaction.commit_unless_managed()
		completed = '^%s' % url
	else:
		completed = None

	# Fetch list of latest purges
	curs = connection.cursor()
	curs.execute("SELECT ev_time, ev_data FROM pgq.event_1 WHERE ev_type='P' ORDER BY ev_time DESC LIMIT 20")
	latest = [{'t': r[0], 'u': r[1]} for r in curs.fetchall()]

	return render_to_response('core/admin_purge.html', {
			'purge_completed': completed,
			'latest_purges': latest,
			})

# Merge two organisations
@login_required
@user_passes_test(lambda u: u.is_superuser)
@transaction.commit_on_success
def admin_mergeorg(request):
	if request.method == 'POST':
		form = MergeOrgsForm(data=request.POST)
		if form.is_valid():
			# Ok, try to actually merge organisations, by moving all objects
			# attached
			f = form.cleaned_data['merge_from']
			t = form.cleaned_data['merge_into']
			for e in f.event_set.all():
				e.org = t
				e.save()
			for n in f.newsarticle_set.all():
				n.org = t
				n.save()
			for p in f.product_set.all():
				p.publisher = t
				p.save()
			for p in f.professionalservice_set.all():
				p.organisation = t
				p.save()
			# Now that everything is moved, we can delete the organisation
			f.delete()
			
			return HttpResponseRedirect("/admin/core/organisation/")
		# Else fall through to re-render form with errors
	else:
		form = MergeOrgsForm()

	return render_to_response('core/admin_mergeorg.html', {
			'form': form,
    })
