import datetime
import time
from email.utils import formatdate, parsedate
import urllib.parse
import requests
import urllib3

from queue import Queue
import threading

from lib.log import log
from lib.parsers import GenericHtmlParser


_orig_create_connection = urllib3.util.connection.create_connection


def override_create_connection(hostname, ipaddr):
    def _override(address, *args, **kwargs):
        host, port = address
        if host == hostname:
            return _orig_create_connection((ipaddr, port), *args, **kwargs)
        else:
            return _orig_create_connection(address, *args, **kwargs)
    urllib3.util.connection.create_connection = _override


class BaseSiteCrawler(object):
    def __init__(self, hostname, dbconn, siteid, serverip=None, https=False):
        self.hostname = hostname
        self.dbconn = dbconn
        self.siteid = siteid
        self.serverip = serverip
        self.https = https
        self.pages_crawled = {}
        self.pages_new = 0
        self.pages_updated = 0
        self.pages_deleted = 0
        self.status_interval = 5

        if serverip:
            override_create_connection(hostname, serverip)

        curs = dbconn.cursor()
        curs.execute("SELECT suburl, lastscanned FROM webpages WHERE site=%(id)s AND lastscanned IS NOT NULL", {'id': siteid})
        self.scantimes = dict(curs.fetchall())
        self.queue = Queue()
        self.counterlock = threading.RLock()
        self.stopevent = threading.Event()

    def crawl(self):
        self.init_crawl()

        # Fire off worker threads
        for x in range(5):
            t = threading.Thread(name="Indexer %s" % x,
                                 target=lambda: self.crawl_from_queue())
            t.daemon = True
            t.start()

        t = threading.Thread(name="statusthread", target=lambda: self.status_thread())
        t.daemon = True
        t.start()

        # XXX: need to find a way to deal with all threads crashed and
        # not done here yet!
        self.queue.join()
        self.stopevent.set()

        # Remove all pages that we didn't crawl
        curs = self.dbconn.cursor()
        curs.execute("DELETE FROM webpages WHERE site=%(site)s AND NOT suburl=ANY(%(urls)s)", {
            'site': self.siteid,
            'urls': list(self.pages_crawled.keys()),
        })
        if curs.rowcount:
            log("Deleted %s pages no longer accessible" % curs.rowcount)
        self.pages_deleted += curs.rowcount

        self.dbconn.commit()
        log("Considered %s pages, wrote %s updated and %s new, deleted %s." % (len(self.pages_crawled), self.pages_updated, self.pages_new, self.pages_deleted))

    def status_thread(self):
        starttime = time.time()
        while not self.stopevent.is_set():
            self.stopevent.wait(self.status_interval)
            nowtime = time.time()
            with self.counterlock:
                log("Considered %s pages, wrote %s upd, %s new, %s del (%s threads, %s in queue, %.1f pages/sec)" % (
                    len(self.pages_crawled),
                    self.pages_updated,
                    self.pages_new,
                    self.pages_deleted,
                    threading.active_count() - 2,
                    self.queue.qsize(),
                    len(self.pages_crawled) / (nowtime - starttime),
                ))

    def crawl_from_queue(self):
        while not self.stopevent.is_set():
            (url, relprio, internal) = self.queue.get()
            try:
                self.crawl_page(url, relprio, internal)
            except Exception as e:
                log("Exception crawling '%s': %s" % (url, e))
            self.queue.task_done()

    def exclude_url(self, url):
        return False

    def crawl_page(self, url, relprio, internal):
        if url in self.pages_crawled or url + "/" in self.pages_crawled:
            return

        if self.exclude_url(url):
            return

        self.pages_crawled[url] = 1
        (result, pagedata, lastmod) = self.fetch_page(url)

        if result == 0:
            if pagedata is None:
                # Result ok but no data, means that the page was not modified.
                # Thus we can happily consider ourselves done here.
                return
        else:
            # Page failed to load or was a redirect, so remove from database
            curs = self.dbconn.cursor()
            curs.execute("DELETE FROM webpages WHERE site=%(id)s AND suburl=%(url)s", {
                'id': self.siteid,
                'url': url,
            })
            with self.counterlock:
                self.pages_deleted += curs.rowcount

            if result == 1:
                # Page was a redirect, so crawl into that page if we haven't
                # already done so.
                self.queue_url(pagedata)
            return

        # Try to convert pagedata to a unicode string
        try:
            self.page = self.parse_html(pagedata)
        except Exception as e:
            log("Failed to parse HTML for %s" % url)
            log(e)
            return

        self.save_page(url, lastmod, relprio, internal)
        self.post_process_page(url)

    def save_page(self, url, lastmod, relprio, internal):
        if relprio == 0.0:
            relprio = 0.5
        params = {
            'title': self.page.title[:128],
            'txt': self.page.gettext(),
            'lastmod': lastmod,
            'site': self.siteid,
            'url': url,
            'relprio': relprio,
            'internal': internal,
        }
        curs = self.dbconn.cursor()
        curs.execute("UPDATE webpages SET title=%(title)s, txt=%(txt)s, fti=setweight(to_tsvector('public.pg', %(title)s), 'A') || to_tsvector('public.pg', %(txt)s), lastscanned=%(lastmod)s, relprio=%(relprio)s, isinternal=%(internal)s WHERE site=%(site)s AND suburl=%(url)s", params)
        if curs.rowcount != 1:
            curs.execute("INSERT INTO webpages (site, suburl, title, txt, fti, lastscanned, relprio, isinternal) VALUES (%(site)s, %(url)s, %(title)s, %(txt)s, setweight(to_tsvector('public.pg', %(title)s), 'A') || to_tsvector('public.pg', %(txt)s), %(lastmod)s, %(relprio)s, %(internal)s)", params)
            with self.counterlock:
                self.pages_new += 1
        else:
            with self.counterlock:
                self.pages_updated += 1

    ACCEPTED_CONTENTTYPES = ("text/html", "text/plain", )

    def accept_contenttype(self, contenttype):
        # Split apart if there is a "; charset=" in it
        if contenttype.find(";"):
            contenttype = contenttype.split(';', 2)[0]
        return contenttype in self.ACCEPTED_CONTENTTYPES

    def fetch_page(self, url):
        try:
            headers = {
                'User-agent': 'pgsearch/0.2',
            }
            if url in self.scantimes:
                headers["If-Modified-Since"] = formatdate(time.mktime(self.scantimes[url].timetuple()))

            if self.serverip and False:
                connectto = self.serverip
                headers['Host'] = self.hostname
            else:
                connectto = self.hostname

            resp = requests.get(
                '{}://{}{}'.format(self.https and 'https' or 'http', connectto, url),
                headers=headers,
                timeout=10,
            )

            if resp.status_code == 200:
                if not self.accept_contenttype(resp.headers["content-type"]):
                    # Content-type we're not interested in
                    return (2, None, None)
                return (0, resp.text, self.get_date(resp.headers.get("last-modified", None)))
            elif resp.status_code == 304:
                # Not modified, so no need to reprocess, but also don't
                # give an error message for it...
                return (0, None, None)
            elif resp.status_code == 301:
                # A redirect... So try again with the redirected-to URL
                # We send this through our link resolver to deal with both
                # absolute and relative URLs
                if resp.headers.get('location', '') == '':
                    log("Url %s returned empty redirect" % url)
                    return (2, None, None)

                for tgt in self.resolve_links([resp.header['location'], ], url):
                    return (1, tgt, None)
                # No redirect at all found, becaue it was invalid?
                return (2, None, None)
            else:
                # print "Url %s returned status %s" % (url, resp.status)
                pass
        except Exception as e:
            log("Exception when loading url %s: %s" % (url, e))
        return (2, None, None)

    def get_date(self, date):
        d = parsedate(date)
        if d:
            return datetime.datetime.fromtimestamp(time.mktime(d))
        return datetime.datetime.now()

    def parse_html(self, page):
        if page is None:
            return None

        p = GenericHtmlParser()
        p.feed(page)
        return p

    def resolve_links(self, links, pageurl):
        for x in links:
            p = urllib.parse.urlsplit(x)
            if p.scheme in ("http", "https"):
                if p.netloc != self.hostname:
                    # Remote link
                    continue
                # Turn this into a host-relative url
                p = ('', '', p.path, p.query, '')

            if p[4] != "" or p[3] != "":
                # Remove fragments (part of the url past #)
                p = (p[0], p[1], p[2], '', '')

            if p[0] == "":
                if p[2] == "":
                    # Nothing in the path, so it's a pure fragment url
                    continue

                if p[2][0] == "/":
                    # Absolute link on this host, so just return it
                    yield urllib.parse.urlunsplit(p)
                else:
                    # Relative link
                    yield urllib.parse.urljoin(pageurl, urllib.parse.urlunsplit(p))
            else:
                # Ignore unknown url schemes like mailto
                pass
