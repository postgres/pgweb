from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from pgweb.util.decorators import cache

import httplib
import urllib
import psycopg2
import json
import socket
import ssl

from pgweb.lists.models import MailingList

# Conditionally import memcached library. Everything will work without
# it, so we allow development installs to run without it...
try:
    import pylibmc
    has_memcached = True
except:
    has_memcached = False


def generate_pagelinks(pagenum, totalpages, querystring):
    # Generate a list of links to page through a search result
    # We generate these in HTML from the python code because it's
    # simply too ugly to try to do it in the template.
    if totalpages < 2:
        return

    if pagenum > 1:
        # Prev link
        yield '<a href="%s&p=%s">Prev</a>' % (querystring, pagenum - 1)

    if pagenum > 10:
        start = pagenum - 10
    else:
        start = 1

    for i in range(start, min(start + 20, totalpages + 1)):
        if i == pagenum:
            yield "%s" % i
        else:
            yield '<a href="%s&p=%s">%s</a>' % (querystring, i, i)

    if pagenum != min(start + 20, totalpages):
        yield '<a href="%s&p=%s">Next</a>' % (querystring, pagenum + 1)


@csrf_exempt
@cache(minutes=15)
def search(request):
    # Perform a general web search
    # Since this lives in a different database, we open a direct
    # connection with psycopg, thus bypassing everything that has to do
    # with django.

    # constants that we might eventually want to make configurable
    hitsperpage = 20

    if request.GET.get('m', '') == '1':
        searchlists = True

        if request.GET.get('l', '') != '':
            try:
                listid = int(request.GET['l'])
            except:
                listid = None
        else:
            # Listid not specified. But do we have the name?
            if 'ln' in request.GET:
                try:
                    ll = MailingList.objects.get(listname=request.GET['ln'])
                    listid = ll.id
                except MailingList.DoesNotExist:
                    # Invalid list name just resets the default of the form,
                    # no need to throw an error.
                    listid = None
            else:
                listid = None

        if 'd' in request.GET:
            try:
                dateval = int(request.GET['d'])
            except:
                dateval = None
        else:
            dateval = None

        if 's' in request.GET:
            listsort = request.GET['s']
            if listsort not in ('r', 'd', 'i'):
                listsort = 'r'
        else:
            listsort = 'r'

        if not dateval:
            dateval = 365

        sortoptions = (
            {'val': 'r', 'text': 'Rank', 'selected': request.GET.get('s', '') not in ('d', 'i')},
            {'val': 'd', 'text': 'Date', 'selected': request.GET.get('s', '') == 'd'},
            {'val': 'i', 'text': 'Reverse date', 'selected': request.GET.get('s', '') == 'i'},
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
        suburl = request.GET.get('u', None)
        allsites = request.GET.get('a', None) == "1"

    # Check that we actually have something to search for
    if request.GET.get('q', '') != '':
        if searchlists:
            return render(request, 'search/listsearch.html', {
                'search_error': "No search term specified.",
                'sortoptions': sortoptions,
                'lists': MailingList.objects.all().order_by("group__sortkey"),
                'listid': listid,
                'dates': dateoptions,
                'dateval': dateval,
            })
        else:
            return render(request, 'search/sitesearch.html', {
                'search_error': "No search term specified.",
            })
    query = request.GET['q'].strip()

    # Anti-stefan prevention
    if len(query) > 1000:
        return render(request, 'search/sitesearch.html', {
            'search_error': "Search term too long.",
        })

    # Is the request being paged?
    try:
        pageum = int(request.GET.get('p', 1))
    except:
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
                p['ln'] = ','.join([x.listname for x in MailingList.objects.filter(group=-listid)])
            else:
                p['ln'] = MailingList.objects.get(pk=listid).listname
        if dateval:
            p['d'] = dateval
        urlstr = urllib.urlencode(p)
        # If memcached is available, let's try it
        hits = None
        if has_memcached:
            memc = pylibmc.Client(['127.0.0.1', ], binary=True)
            # behavior not supported on pylibmc in squeeze:: behaviors={'tcp_nodelay':True})
            try:
                hits = memc.get(urlstr)
            except Exception:
                # If we had an exception, don't try to store either
                memc = None
        if not hits:
            # No hits found - so try to get them from the search server
            if settings.ARCHIVES_SEARCH_PLAINTEXT:
                c = httplib.HTTPConnection(settings.ARCHIVES_SEARCH_SERVER, strict=True, timeout=5)
            else:
                c = httplib.HTTPSConnection(settings.ARCHIVES_SEARCH_SERVER, strict=True, timeout=5)
            c.request('POST', '/archives-search/', urlstr, {'Content-type': 'application/x-www-form-urlencoded; charset=utf-8'})
            c.sock.settimeout(20)  # Set a 20 second timeout
            try:
                r = c.getresponse()
            except (socket.timeout, ssl.SSLError):
                return render(request, 'search/listsearch.html', {
                    'search_error': 'Timeout when talking to search server. Please try your search again later, or with a more restrictive search terms.',
                })
            if r.status != 200:
                memc = None
                return render(request, 'search/listsearch.html', {
                    'search_error': 'Error talking to search server: %s' % r.reason,
                })
            hits = json.loads(r.read())
            if has_memcached and memc:
                # Store them in memcached too! But only for 10 minutes...
                # And always compress it, just because we can
                memc.set(urlstr, hits, 60 * 10, 1)
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

        return render(request, 'search/listsearch.html', {
            'hitcount': totalhits,
            'firsthit': firsthit,
            'lasthit': min(totalhits, firsthit + hitsperpage - 1),
            'query': request.GET['q'],
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
            } for h in hits[firsthit - 1:firsthit + hitsperpage - 1]],
            'sortoptions': sortoptions,
            'lists': MailingList.objects.all().order_by("group__sortkey"),
            'listid': listid,
            'dates': dateoptions,
            'dateval': dateval,
        })

    else:
        # Website search is still done by making a regular pgsql connection
        # to the search server.
        try:
            conn = psycopg2.connect(settings.SEARCH_DSN)
            curs = conn.cursor()
        except:
            return render(request, 'search/sitesearch.html', {
                'search_error': 'Could not connect to search database.'
            })

        # This is kind of a hack, but... Some URLs are flagged as internal
        # and should as such only be included in searches that explicitly
        # reference the suburl that they are in.
        if suburl and suburl.startswith('/docs/devel'):
            include_internal = True
        else:
            include_internal = False

        # perform the query for general web search
        try:
            curs.execute("SELECT * FROM site_search(%(query)s, %(firsthit)s, %(hitsperpage)s, %(allsites)s, %(suburl)s, %(internal)s)", {
                'query': query,
                'firsthit': firsthit - 1,
                'hitsperpage': hitsperpage,
                'allsites': allsites,
                'suburl': suburl,
                'internal': include_internal,
            })
        except psycopg2.ProgrammingError:
            return render(request, 'search/sitesearch.html', {
                'search_error': 'Error executing search query.'
            })

        hits = curs.fetchall()
        conn.close()
        totalhits = int(hits[-1][5])
        try:
            if suburl:
                quoted_suburl = urllib.quote_plus(suburl)
            else:
                quoted_suburl = ''
        except:
            quoted_suburl = ''
        querystr = "?q=%s&a=%s&u=%s" % (
            urllib.quote_plus(query.encode('utf-8')),
            allsites and "1" or "0",
            quoted_suburl,
        )

        return render(request, 'search/sitesearch.html', {
            'suburl': suburl,
            'allsites': allsites,
            'hitcount': totalhits,
            'firsthit': firsthit,
            'lasthit': min(totalhits, firsthit + hitsperpage - 1),
            'query': request.GET['q'],
            'pagelinks': "&nbsp;".join(
                generate_pagelinks(pagenum,
                                   totalhits / hitsperpage + 1,
                                   querystr)),
            'hits': [{
                'title': h[3],
                'url': "%s%s" % (h[1], h[2]),
                'abstract': h[4].replace("[[[[[[", "<strong>").replace("]]]]]]", "</strong>"),
                'rank': h[5]} for h in hits[:-1]],
        })
