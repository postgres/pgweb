from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from pgweb.util.decorators import cache

import httplib
import urllib
import psycopg2
import simplejson as json
import socket

from lists.models import MailingList

# Conditionally import memcached library. Everything will work without
# it, so we allow development installs to run without it...
try:
	import pylibmc
	has_memcached=True
except:
	has_memcached=False

def generate_pagelinks(pagenum, totalpages, querystring):
	# Generate a list of links to page through a search result
	# We generate these in HTML from the python code because it's
	# simply too ugly to try to do it in the template.
	if totalpages < 2:
		return

	if pagenum > 1:
		# Prev link
		yield '<a href="%s&p=%s">Prev</a>' % (querystring, pagenum-1)

	if pagenum > 10:
		start = pagenum - 10
	else:
		start = 1

	for i in range(start, min(start+20, totalpages + 1)):
		if i == pagenum:
			yield "%s" % i
		else:
			yield '<a href="%s&p=%s">%s</a>' % (querystring, i, i)

	if pagenum != min(start+20, totalpages):
		yield '<a href="%s&p=%s">Next</a>' % (querystring, pagenum+1)


@csrf_exempt
@cache(minutes=15)
def search(request):
	# Perform a general web search
	# Since this lives in a different database, we open a direct
	# connection with psycopg, thus bypassing everything that has to do
	# with django.

	# constants that we might eventually want to make configurable
	hitsperpage = 20

	if request.REQUEST.has_key('m') and request.REQUEST['m'] == '1':
		searchlists = True

		if request.REQUEST.has_key('l'):
			if request.REQUEST['l'] != '':
				try:
					listid = int(request.REQUEST['l'])
				except:
					listid = None
			else:
				listid = None
		else:
			listid = None

		if request.REQUEST.has_key('d'):
			try:
				dateval = int(request.REQUEST['d'])
			except:
				dateval = None
		else:
			dateval = None

		if request.REQUEST.has_key('s'):
			listsort = request.REQUEST['s']
			if not listsort in ('r', 'd', 'i'):
				listsort = 'r'
		else:
			listsort = 'r'

		if not dateval:
			dateval = 365

		sortoptions = (
			{'val':'r', 'text': 'Rank', 'selected': not (request.REQUEST.has_key('s') and request.REQUEST['s'] == 'd')},
			{'val':'d', 'text': 'Date', 'selected': request.REQUEST.has_key('s') and request.REQUEST['s'] == 'd'},
			{'val':'i', 'text': 'Reverse date', 'selected': request.REQUEST.has_key('s') and request.REQUEST['s'] == 'i'},
			)
		dateoptions = (
			{'val': -1, 'text': 'anytime'},
			{'val': 1, 'text': 'within last day'},
			{'val': 7, 'text': 'within last week'},
			{'val': 31, 'text': 'within last month'},
			{'val': 186, 'text': 'within last 6 months'},
			{'val': 365, 'text': 'within last year'},
			)
	else:
		searchlists = False
		if request.REQUEST.has_key('u'):
			suburl = request.REQUEST['u']
		else:
			suburl = None

		if request.REQUEST.has_key('a'):
			allsites = (request.REQUEST['a'] == "1")
		else:
			allsites = False

	# Check that we actually have something to search for
	if not request.REQUEST.has_key('q') or request.REQUEST['q'] == '':
		if searchlists:
			return render_to_response('search/listsearch.html', {
					'search_error': "No search term specified.",
					'sortoptions': sortoptions,
					'lists': MailingList.objects.all().order_by("group__sortkey"),
					'listid': listid,
					'dates': dateoptions,
					'dateval': dateval,
					}, RequestContext(request))
		else:
			return render_to_response('search/sitesearch.html', {
					'search_error': "No search term specified.",
					}, RequestContext(request))
	query = request.REQUEST['q']

	# Anti-stefan prevention
	if len(query) > 1000:
		return render_to_response('search/sitesearch.html', {
			'search_error': "Search term too long.",
			}, RequestContext(request))

	# Is the request being paged?
	if request.REQUEST.has_key('p'):
		try:
			pagenum = int(request.REQUEST['p'])
		except:
			pagenum = 1
	else:
		pagenum = 1

	firsthit = (pagenum - 1) * hitsperpage + 1

	if searchlists:
		# Lists are searched by passing the work down using a http
		# API. In the future, we probably want to do everything
		# through a http API and merge hits, but that's for later
		p = {
			'q': query.encode('utf-8'),
			's': listsort,
			}
		if listid:
			if listid < 0:
				# This is a list group, we expand that on the web server
				p['l'] = ','.join([str(x.id) for x in MailingList.objects.filter(group=-listid)])
			else:
				p['l'] = listid
		if dateval:
			p['d'] = dateval
		urlstr = urllib.urlencode(p)
		# If memcached is available, let's try it
		hits = None
		if has_memcached:
			memc = pylibmc.Client(['127.0.0.1',], binary=True)
			# behavior not supported on pylibmc in squeeze:: behaviors={'tcp_nodelay':True})
			try:
				hits = memc.get(urlstr)
			except Exception:
				# If we had an exception, don't try to store either
				memc = None
		if not hits:
			# No hits found - so try to get them from the search server
			c = httplib.HTTPConnection(settings.ARCHIVES_SEARCH_SERVER, strict=True, timeout=5)
			c.request('POST', '/archives-search/', urlstr)
			c.sock.settimeout(20) # Set a 20 second timeout
			try:
				r = c.getresponse()
			except socket.timeout:
				return render_to_response('search/listsearch.html', {
						'search_error': 'Timeout when talking to search server. Please try your search again later, or with a more restrictive search terms.',
						}, RequestContext(request))
			if r.status != 200:
				memc = None
				return render_to_response('search/listsearch.html', {
						'search_error': 'Error talking to search server: %s' % r.reason,
						}, RequestContext(request))
			hits = json.loads(r.read())
			if has_memcached and memc:
				# Store them in memcached too! But only for 10 minutes...
				# And always compress it, just because we can
				memc.set(urlstr, hits, 60*10, 1)
				memc = None

		if isinstance(hits, dict):
			# This is not just a list of hits.
			# Right now the only supported dict result is a messageid
			# match, but make sure that's what it is.
			if hits['messageidmatch'] == 1:
				return HttpResponseRedirect("/message-id/%s" % query)

		totalhits = len(hits)
		querystr = "?m=1&q=%s&l=%s&d=%s&s=%s" % (
			urllib.quote_plus(query.encode('utf-8')),
			listid or '',
			dateval,
			listsort
			)

		return render_to_response('search/listsearch.html', {
				'hitcount': totalhits,
				'firsthit': firsthit,
				'lasthit': min(totalhits, firsthit+hitsperpage-1),
				'query': request.REQUEST['q'],
				'pagelinks': "&nbsp;".join(
					generate_pagelinks(pagenum,
									   totalhits / hitsperpage + 1,
									   querystr)),
				'hits': [{
						'date': h['d'],
						'subject': h['s'],
						'author': h['f'],
						'messageid': h['m'],
						'abstract': h['a'],
						'rank': h['r'],
						} for h in hits[firsthit-1:firsthit+hitsperpage-1]],
				'sortoptions': sortoptions,
				'lists': MailingList.objects.all().order_by("group__sortkey"),
				'listid': listid,
				'dates': dateoptions,
				'dateval': dateval,
				}, RequestContext(request))

	else:
		# Website search is still done by making a regular pgsql connection
		# to the search server.
		try:
			conn = psycopg2.connect(settings.SEARCH_DSN)
			curs = conn.cursor()
		except:
			return render_to_response('search/sitesearch.html', {
					'search_error': 'Could not connect to search database.'
					}, RequestContext(request))

		# perform the query for general web search
		curs.execute("SELECT * FROM site_search(%(query)s, %(firsthit)s, %(hitsperpage)s, %(allsites)s, %(suburl)s)", {
				'query': query,
				'firsthit': firsthit - 1,
				'hitsperpage': hitsperpage,
				'allsites': allsites,
				'suburl': suburl
				})

		hits = curs.fetchall()
		conn.close()
		totalhits = int(hits[-1][5])
		querystr = "?q=%s&a=%s&u=%s" % (
			urllib.quote_plus(query.encode('utf-8')),
			allsites and "1" or "0",
			suburl and urllib.quote_plus(suburl) or '',
			)

		return render_to_response('search/sitesearch.html', {
				'suburl': suburl,
				'allsites': allsites,
				'hitcount': totalhits,
				'firsthit': firsthit,
				'lasthit': min(totalhits, firsthit+hitsperpage-1),
				'query': request.REQUEST['q'],
				'pagelinks': "&nbsp;".join(
					generate_pagelinks(pagenum,
									   totalhits / hitsperpage + 1,
									   querystr)),
				'hits': [{
						'title': h[3],
						'url': "%s%s" % (h[1], h[2]),
						'abstract': h[4].replace("[[[[[[", "<b>").replace("]]]]]]","</b>"),
						'rank': h[5]} for h in hits[:-1]],
				}, RequestContext(request))
