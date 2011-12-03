from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.conf import settings

from pgweb.util.decorators import cache

import datetime
import urllib
import psycopg2

from lists.models import MailingList, MailingListGroup


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
				listid = int(request.REQUEST['l'])
			else:
				listid = None
		else:
			listid = None

		if request.REQUEST.has_key('d'):
			dateval = int(request.REQUEST['d'])
		else:
			dateval = None

		if request.REQUEST.has_key('s'):
			listsort = request.REQUEST['s']
		else:
			listsort = 'r'

		if dateval == -1:
			firstdate = None
		else:
			firstdate = datetime.datetime.today()-datetime.timedelta(days=dateval)

		sortoptions = (
			{'val':'r', 'text': 'Rank', 'selected': not (request.REQUEST.has_key('s') and request.REQUEST['s'] == 'd')},
			{'val':'d', 'text': 'Date', 'selected': request.REQUEST.has_key('s') and request.REQUEST['s'] == 'd'},
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
					})
		else:
			return render_to_response('search/sitesearch.html', {
					'search_error': "No search term specified.",
					})
	query = request.REQUEST['q']

	# Is the request being paged?
	if request.REQUEST.has_key('p'):
		try:
			pagenum = int(request.REQUEST['p'])
		except:
			pagenum = 1
	else:
		pagenum = 1

	firsthit = (pagenum - 1) * hitsperpage + 1

	# Get ourselves a connection
	try:
		conn = psycopg2.connect(settings.SEARCH_DSN)
		curs = conn.cursor()
	except:
		return render_to_response('search/sitesearch.html', {
				'search_error': 'Could not connect to search database.'
				})

	if searchlists:
		# perform the query for list archives search
		curs.execute("SELECT * from archives_search(%(query)s, %(listid)s, %(firstdate)s, NULL, %(firsthit)s, %(hitsperpage)s, %(sort)s)", {
				'query': query,
				'firsthit': firsthit - 1,
				'hitsperpage': hitsperpage,
				'listid': listid,
				'firstdate': firstdate,
				'sort': listsort,
				})
		hits = curs.fetchall()
		conn.close()
		totalhits = int(hits[-1][1])
		querystr = "?m=1&q=%s&l=%s&d=%s&s=%s" % (
			urllib.quote_plus(query),
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
						'list': h[0],
						'year': h[1],
						'month': h[2],
						'msgnum': "%05d" % h[3],
						'date': h[4],
						'subject': h[5],
						'author': h[6],
						'abstract': h[7].replace("[[[[[[", "<b>").replace("]]]]]]","</b>"),
						'rank': h[8],
						} for h in hits[:-1]],
				'sortoptions': sortoptions,
				'lists': MailingList.objects.all().order_by("group__sortkey"),
				'listid': listid,
				'dates': dateoptions,
				'dateval': dateval,
				})
	else:
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
			urllib.quote_plus(query),
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
				})
