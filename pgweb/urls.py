from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

# Register our save signal handlers
from pgweb.util.bases import register_basic_signal_handlers
register_basic_signal_handlers()

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


# dict with all the RSS feeds we can serve
from core.feeds import VersionFeed
from news.feeds import NewsFeed
from events.feeds import EventFeed
from pwn.feeds import PwnFeed
feeds = {
	'versions': VersionFeed,
	'news': NewsFeed,
	'events': EventFeed,
	'weeklynews': PwnFeed,
}

urlpatterns = patterns('',
    (r'^$', 'pgweb.core.views.home'),

    (r'^about/newsarchive/$', 'news.views.archive'),
    (r'^about/news/(\d+)(-.*)?/$', 'news.views.item'),
    (r'^about/events/$', 'events.views.main'),
    (r'^about/eventarchive/$', 'events.views.archive'),
    (r'^about/eventarchive/training/$', 'events.views.trainingarchive'),
    (r'^about/event/(\d+)(-.*)?/$', 'events.views.item'),
    (r'^about/featurematrix/$', 'featurematrix.views.root'),
    (r'^about/featurematrix/detail/(\d+)/$', 'featurematrix.views.detail'),
    (r'^about/quotesarchive/$', 'quotes.views.allquotes'),
    
    (r'^ftp/(.*/)?$', 'downloads.views.ftpbrowser'),
    (r'^download/mirrors-ftp/+(.*)$', 'downloads.views.mirrorselect'),
    (r'^download/product-categories/$', 'downloads.views.categorylist'),
    (r'^download/products/(\d+)(-.*)?/$', 'downloads.views.productlist'),
    (r'^redir/(\d+)/([hf])/([a-zA-Z0-9/\._-]+)$', 'downloads.views.mirror_redirect'),
    (r'^redir$', 'downloads.views.mirror_redirect_old'),
    (r'^mirrors.xml$', 'downloads.views.mirrors_xml'),
    (r'^applications-v2.xml$', 'downloads.views.applications_v2_xml'),
    (r'^download/uploadftp/', 'downloads.views.uploadftp'),

    (r'^docs/(current|devel|\d\.\d)/(static|interactive)/(.*).html?$', 'docs.views.docpage'),
    (r'^docs/(current|devel|\d\.\d)/(static|interactive)/$', 'docs.views.docsrootpage'),
    (r'^docs/(current|devel|\d\.\d)/$', 'docs.views.redirect_root'),

    (r'^community/$', 'core.views.community'),
    (r'^community/contributors/$', 'contributors.views.completelist'),
    (r'^community/lists/$', 'lists.views.root'),
    (r'^community/lists/subscribe/$', 'lists.views.subscribe'),
    (r'^community/lists/listinfo/$', 'lists.views.listinfo'),
    (r'^community/survey/vote/(\d+)/$', 'survey.views.vote'),
    (r'^community/survey[/\.](\d+)(-.*)?/$', 'survey.views.results'),
	(r'^community/weeklynews/$', 'pwn.views.index'),
	(r'^community/weeklynews/pwn(\d{4})(\d{2})(\d{2})/$', 'pwn.views.post'),

    (r'^search/$', 'search.views.search'),

    (r'^support/professional_(support|hosting)/$', 'profserv.views.root'),
    (r'^support/professional_(support|hosting)[/_](.*)/$', 'profserv.views.region'),
    (r'^support/submitbug/$', 'misc.views.submitbug'),
    (r'^support/versioning/$', 'core.views.versions'),

    (r'^about/sponsors/$', 'pgweb.sponsors.views.sponsors'),
    (r'^about/servers/$', 'pgweb.sponsors.views.servers'),

	(r'^robots.txt$', 'pgweb.core.views.robots'),

    ###
    # RSS feeds
    ###
    (r'^(versions|news|events|weeklynews).rss$', 'django.contrib.syndication.views.feed', {'feed_dict':feeds}),

    ###
    # Special sections
    ###
    (r'^account/', include('account.urls')),

	###
	# Sitemap (FIXME: support for >50k urls!)
	###
	(r'^sitemap.xml', 'pgweb.core.views.sitemap'),

    ###
    # Workaround for broken links pushed in press release
    ###
    (r'^downloads/$', redirect_to, {'url': '/download/'}),

    ###
    # Legacy URLs from the old website, that are likely to be used from other
    # sites or press releases or such
    ###
    (r'^about/press/presskit(\d+)\.html\.(\w+)$', 'pgweb.legacyurl.views.presskit'),
    (r'^about/news\.(\d+)$', 'pgweb.legacyurl.views.news'),
    (r'^about/event\.(\d+)$', 'pgweb.legacyurl.views.event'),
    (r'^community/signup', 'pgweb.legacyurl.views.signup'),

    ###
    # Images that are used from other community sites
    ###
    (r'^layout/images/(?P<f>[a-z0-9_\.]+)$', redirect_to, {'url': '/media/img/layout/%(f)s' }),
    ###
    # These URLs were legacy even on the old site...
    ###
    (r'^developer/sourcecode/$', redirect_to, {'url': '/developer/coding/' }),
    (r'^developer/bios/$', redirect_to, {'url': '/community/contributors/' }),
    (r'^docs/techdocs.*', redirect_to, {'url': 'http://wiki.postgresql.org/' }),
    (r'^docs/faqs.FAQ.html$', redirect_to, {'url': 'http://wiki.postgresql.org/wiki/FAQ' }),
    (r'^docs/faqs.FAQ_DEV.*', redirect_to, {'url': 'http://wiki.postgresql.org/wiki/Development_information' }),
    (r'^docs/faqs.TODO.*', redirect_to, {'url': 'http://wiki.postgresql.org/wiki/Todo' }),
    (r'^about/license/$', redirect_to, {'url': '/about/licence'}),

    ###
    # Links included in emails on the lists (do we need to check this for XSS?)
    ###
    (r'^mailpref/([a-z0-9_-]+)/$', 'pgweb.legacyurl.views.mailpref'),

    # Some basic information about the connection (for debugging purposes)
	(r'^system_information/$', 'pgweb.core.views.system_information'),
	# Sync timestamp, for automirror
	(r'^web_sync_timestamp$', 'pgweb.core.views.sync_timestamp'),

    # API endpoints
    (r'^api/varnish/purge/$', 'pgweb.core.views.api_varnish_purge'),

	# Override some URLs in admin, to provide our own pages
	(r'^admin/pending/$', 'pgweb.core.views.admin_pending'),
	(r'^admin/purge/$', 'pgweb.core.views.admin_purge'),
	(r'^admin/mergeorg/$', 'pgweb.core.views.admin_mergeorg'),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    # This should not happen in production - serve by the webserver natively!
    url(r'^media/(.*)$', 'django.views.static.serve', {
        'document_root': '../media',
    }),
    url(r'^(favicon.ico)$', 'django.views.static.serve', {
        'document_root': '../media',
    }),

    # Crash testing URL :-)
    (r'^crashtest/$', 'pgweb.misc.views.crashtest'),

	# If we're getting an attempt for something ending in HTML, just get rid of it
	(r'^(.*)\.html$', 'pgweb.legacyurl.views.html_extension'),

    # Fallback for static pages, must be at the bottom
    (r'^(.*)/$', 'pgweb.core.views.fallback'),
)

