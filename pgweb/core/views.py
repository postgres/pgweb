from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.http import HttpResponseNotModified
from django.template import TemplateDoesNotExist, loader
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.db import connection, transaction
from django.utils.http import http_date, parse_http_date
from django.conf import settings

from datetime import date, datetime
import os
import re
import urllib

from pgweb.util.decorators import cache, nocache
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form, PgXmlHelper, HttpServerError
from pgweb.util.moderation import get_all_pending_moderations
from pgweb.util.misc import get_client_ip, is_behind_cache, varnish_purge
from pgweb.util.sitestruct import get_all_pages_struct

# models needed for the pieces on the frontpage
from pgweb.news.models import NewsArticle
from pgweb.events.models import Event
from pgweb.quotes.models import Quote
from models import Version, ImportedRSSItem

# models needed for the pieces on the community page
from pgweb.survey.models import Survey

# models and forms needed for core objects
from models import Organisation
from forms import OrganisationForm, MergeOrgsForm
from django.template.context import RequestContext

# Front page view
@cache(minutes=10)
def home(request):
	news = NewsArticle.objects.filter(approved=True)[:7]
	events = Event.objects.select_related('country').filter(approved=True, training=False, enddate__gte=date.today()).order_by('enddate', 'startdate')[:5]
	try:
		quote = Quote.objects.filter(approved=True).order_by('?')[0]
	except:
		# if there is no quote available, just ignore error
		quote = None
	versions = Version.objects.filter(supported=True)
	planet = ImportedRSSItem.objects.filter(feed__internalname="planet").order_by("-posttime")[:7]

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
	}, RequestContext(request))

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

# List of supported versions
def versions(request):
	return render_to_response('support/versioning.html', {
			'versions': Version.objects.filter(tree__gt=0).filter(testing=0),
	}, NavContext(request, 'support'))

re_staticfilenames = re.compile("^[0-9A-Z/_-]+$", re.IGNORECASE)
# Generic fallback view for static pages
def fallback(request, url):
	if url.find('..') > -1:
		raise Http404('Page not found.')

	if not re_staticfilenames.match(url):
		raise Http404('Page not found.')

	try:
		t = loader.get_template('pages/%s.html' % url)
	except TemplateDoesNotExist:
		try:
			t = loader.get_template('pages/%s/en.html' % url)
		except TemplateDoesNotExist:
			raise Http404('Page not found.')
		
	# Guestimate the nav section by looking at the URL and taking the first
	# piece of it.
	try:
		navsect = url.split('/',2)[0]
	except:
		navsect = ''
	return HttpResponse(t.render(NavContext(request, navsect)))

# Edit-forms for core objects
@login_required
def organisationform(request, itemid):
	return simple_form(Organisation, itemid, request, OrganisationForm,
					   redirect='/account/edit/organisations/')

# robots.txt
def robots(request):
	if not is_behind_cache(request):
		# If we're not serving this through one of our Varnish caches, we allow *nothing* to be indexed
		return HttpResponse("User-agent: *\nDisallow: /\n", content_type='text/plain')
	else:
		# Regular website
		return HttpResponse("""User-agent: *
Disallow: /admin/
Disallow: /account/
Disallow: /docs/devel/
Disallow: /list/
Disallow: /search/
Disallow: /message-id/raw/
Disallow: /message-id/flat/

Sitemap: https://www.postgresql.org/sitemap.xml
""", content_type='text/plain')


# Sitemap (XML format)
@cache(hours=6)
def sitemap(request):
	resp = HttpResponse(content_type='text/xml')
	x = PgXmlHelper(resp)
	x.startDocument()
	x.startElement('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})
	pages = 0
	for p in get_all_pages_struct():
		pages+=1
		x.startElement('url', {})
		x.add_xml_element('loc', 'https://www.postgresql.org/%s' % urllib.quote(p[0]))
		if len(p) > 1 and p[1]:
			x.add_xml_element('priority', unicode(p[1]))
		if len(p) > 2 and p[2]:
			x.add_xml_element('lastmod', p[2].isoformat() + "Z")
		x.endElement('url')
	x.endElement('urlset')
	x.endDocument()
	return resp

# dynamic CSS serving, meaning we merge a number of different CSS into a
# single one, making sure it turns into a single http response. We do this
# dynamically, since the output will be cached.
_dynamic_cssmap = {
	'base': ['media/css/global.css',
			 'media/css/layout.css',
			 'media/css/text.css',
			 'media/css/navigation.css',
			 'media/css/table.css',
			 'media/css/iefixes.css'],
	'docs': ['media/css/global.css',
			 'media/css/table.css',
			 'media/css/text.css',
		     'media/css/docs.css'],
	}

@cache(hours=6)
def dynamic_css(request, css):
	if not _dynamic_cssmap.has_key(css):
		raise Http404('CSS not found')
	files = _dynamic_cssmap[css]
	resp = HttpResponse(content_type='text/css')

	# We honor if-modified-since headers by looking at the most recently
	# touched CSS file.
	latestmod = 0
	for fn in files:
		try:
			stime = os.stat(fn).st_mtime
			if latestmod < stime:
				latestmod = stime
		except OSError:
			# If we somehow referred to a file that didn't exist, or
			# one that we couldn't access.
			raise Http404('CSS (sub) not found')
	if request.META.has_key('HTTP_IF_MODIFIED_SINCE'):
		# This code is mostly stolen from django :)
		matches = re.match(r"^([^;]+)(; length=([0-9]+))?$",
						   request.META.get('HTTP_IF_MODIFIED_SINCE'),
						   re.IGNORECASE)
		header_mtime = parse_http_date(matches.group(1))
		# We don't do length checking, just the date
		if int(latestmod) <= header_mtime:
			return HttpResponseNotModified(content_type='text/css')
	resp['Last-Modified'] = http_date(latestmod)

	for fn in files:
		with open(fn) as f:
			resp.write("/* %s */\n" % fn)
			resp.write(f.read())
			resp.write("\n")

	return resp

@nocache
def csrf_failure(request, reason=''):
	resp = render_to_response('errors/csrf_failure.html', {
			'reason': reason,
			})
	resp.status_code = 403 # Forbidden
	return resp

# Basic information about the connection
@cache(seconds=30)
def system_information(request):
	return render_to_response('core/system_information.html', {
			'server': os.uname()[1],
			'behind_cache': is_behind_cache(request),
			'cache_server': is_behind_cache(request) and request.META['REMOTE_ADDR'] or None,
			'client_ip': get_client_ip(request),
	})

def system_information_ssl(request):
	return render_to_response('core/system_information.html', {
			'server': os.uname()[1],
			'behind_cache': False,
			'cache_server': None,
			'client_ip': get_client_ip(request),
	})

# Sync timestamp for automirror. Keep it around for 30 seconds
# Basically just a check that we can access the backend still...
@cache(seconds=30)
def sync_timestamp(request):
	s = datetime.now().strftime("%Y-%m-%d %H:%M:%S\n")
	r = HttpResponse(s,	content_type='text/plain')
	r['Content-Length'] = len(s)
	return r

# List of all unapproved objects, for the special admin page
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_pending(request):
	return render_to_response('core/admin_pending.html', {
			'app_list': get_all_pending_moderations(),
			}, RequestContext(request))

# Purge objects from varnish, for the admin pages
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_purge(request):
	if request.method == 'POST':
		url = request.POST['url']
		if url == '':
			return HttpResponseRedirect('.')
		varnish_purge(url)
		messages.info(request, "Purge completed: '^%s'" % url)
		return HttpResponseRedirect('.')

	# Fetch list of latest purges
	curs = connection.cursor()
	curs.execute("SELECT added, completed, consumer, mode, expr FROM varnishqueue.queue q LEFT JOIN varnishqueue.consumers c ON c.consumerid=q.consumerid ORDER BY added DESC")
	latest = curs.fetchall()

	return render_to_response('core/admin_purge.html', {
			'latest_purges': latest,
			}, RequestContext(request))

@csrf_exempt
def api_varnish_purge(request):
	if not request.META['REMOTE_ADDR'] in settings.VARNISH_PURGERS:
		return HttpServerError("Invalid client address")
	if request.method != 'POST':
		return HttpServerError("Can't use this way")
	n = int(request.POST['n'])
	curs = connection.cursor()
	for i in range(0, n):
		expr = request.POST['p%s' % i]
		curs.execute("SELECT varnish_purge_expr(%s)", (expr, ))
	return HttpResponse("Purged %s entries\n" % n)

@nocache
@csrf_exempt
def api_repo_updated(request):
	if not get_client_ip(request) in settings.SITE_UPDATE_HOSTS:
		return HttpServerError("Invalid client address")
	# Ignore methods and contents, just drop the trigger
	open(settings.SITE_UPDATE_TRIGGER_FILE, 'a').close()
	return HttpResponse("OK")

# Merge two organisations
@login_required
@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
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
				p.org = t
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
    }, RequestContext(request))
