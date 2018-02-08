from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

# Register our save signal handlers
from pgweb.util.signals import register_basic_signal_handlers
register_basic_signal_handlers()

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


# dict with all the RSS feeds we can serve
from pgweb.core.feeds import VersionFeed
from pgweb.news.feeds import NewsFeed
from pgweb.events.feeds import EventFeed

urlpatterns = patterns('',
	(r'^$', 'pgweb.core.views.home'),
	(r'^dyncss/(?P<css>base|docs).css$', 'pgweb.core.views.dynamic_css'),

	(r'^about/newsarchive/([^/]+/)?$', 'pgweb.news.views.archive'),
	(r'^about/news/(\d+)(-.*)?/$', 'pgweb.news.views.item'),
	(r'^about/news/taglist.json/$', 'pgweb.news.views.taglist_json'),
	(r'^about/events/$', 'pgweb.events.views.main'),
	(r'^about/eventarchive/$', 'pgweb.events.views.archive'),
	(r'^about/eventarchive/training/$', 'pgweb.events.views.trainingarchive'),
	(r'^about/event/(\d+)(-.*)?/$', 'pgweb.events.views.item'),
	(r'^about/featurematrix/$', 'pgweb.featurematrix.views.root'),
	(r'^about/featurematrix/detail/(\d+)/$', 'pgweb.featurematrix.views.detail'),
	(r'^about/quotesarchive/$', 'pgweb.quotes.views.allquotes'),

	(r'^ftp/(.*/)?$', 'pgweb.downloads.views.ftpbrowser'),
	(r'^download/mirrors-ftp/+(.*)$', 'pgweb.downloads.views.mirrorselect'),
	(r'^download/product-categories/$', 'pgweb.downloads.views.categorylist'),
	(r'^download/products/(\d+)(-.*)?/$', 'pgweb.downloads.views.productlist'),
	(r'^applications-v2.xml$', 'pgweb.downloads.views.applications_v2_xml'),
	(r'^download/uploadftp/', 'pgweb.downloads.views.uploadftp'),
	(r'^download/uploadyum/', 'pgweb.downloads.views.uploadyum'),
	(r'^download/js/yum.js', 'pgweb.downloads.views.yum_js'),

	(r'^docs/$', 'pgweb.docs.views.root'),
	(r'^docs/manuals/$', 'pgweb.docs.views.manuals'),
	(r'^docs/manuals/archive/$', 'pgweb.docs.views.manualarchive'),
	(r'^docs/(current|devel|\d+(?:\.\d)?)/(static|interactive)/(.*).html?$', 'pgweb.docs.views.docpage'),
	(r'^docs/(current|devel|\d+(?:\.\d)?)/(static|interactive)/$', 'pgweb.docs.views.docsrootpage'),
	(r'^docs/(current|devel|\d+(?:\.\d)?)/$', 'pgweb.docs.views.redirect_root'),

	(r'^community/$', 'pgweb.core.views.community'),
	(r'^community/contributors/$', 'pgweb.contributors.views.completelist'),
	(r'^community/lists/$', RedirectView.as_view(url='/list/', permanent=True)),
	(r'^community/lists/subscribe/$', RedirectView.as_view(url='https://lists.postgresql.org/', permanent=True)),

	(r'^community/lists/listinfo/$', 'pgweb.lists.views.listinfo'),
	(r'^community/lists/activate/$', 'pgweb.lists.views.activate'),
	(r'^community/survey/vote/(\d+)/$', 'pgweb.survey.views.vote'),
	(r'^community/survey[/\.](\d+)(-.*)?/$', 'pgweb.survey.views.results'),
	(r'^community/user-groups/$', 'pgweb.pugs.views.index'),

	(r'^search/$', 'pgweb.search.views.search'),

	(r'^support/security/$', 'pgweb.security.views.index'),
	(r'^support/security/([\d\.]+)/$', 'pgweb.security.views.version'),
	(r'^support/security_archive/$', RedirectView.as_view(url='/support/security/', permanent=True)),

	(r'^support/professional_(support|hosting)/$', 'pgweb.profserv.views.root'),
	(r'^support/professional_(support|hosting)[/_](.*)/$', 'pgweb.profserv.views.region'),
	(r'^account/submitbug/$', 'pgweb.misc.views.submitbug'),
	(r'^support/submitbug/$', RedirectView.as_view(url='/account/submitbug/', permanent=True)),
	(r'^support/versioning/$', 'pgweb.core.views.versions'),

	(r'^about/sponsors/$', 'pgweb.sponsors.views.sponsors'),
	(r'^about/servers/$', 'pgweb.sponsors.views.servers'),

	(r'^robots.txt$', 'pgweb.core.views.robots'),

	###
	# RSS feeds
	###
	(r'^versions.rss$', VersionFeed()),
	(r'^news(/(?P<tagurl>[^/]+))?.rss$', NewsFeed()),
	(r'^events.rss$', EventFeed()),

	###
	# Special sections
	###
	(r'^account/', include('pgweb.account.urls')),

	###
	# Sitemap (FIXME: support for >50k urls!)
	###
	(r'^sitemap.xml', 'pgweb.core.views.sitemap'),
	(r'^sitemap_internal.xml', 'pgweb.core.views.sitemap_internal'),

	###
	# Workaround for broken links pushed in press release
	###
	(r'^downloads/$', RedirectView.as_view(url='/download/', permanent=True)),

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
	(r'^layout/images/(?P<f>[a-z0-9_\.]+)$', RedirectView.as_view(url='/media/img/layout/%(f)s', permanent=True)),
	###
	# These URLs were legacy even on the old site...
	###
	(r'^developer/sourcecode/$', RedirectView.as_view(url='/developer/coding/', permanent=True)),
	(r'^developer/bios/$', RedirectView.as_view(url='/community/contributors/', permanent=True)),
	(r'^docs/techdocs.*', RedirectView.as_view(url='https://wiki.postgresql.org/', permanent=True)),
	(r'^docs/faqs.FAQ.html$', RedirectView.as_view(url='https://wiki.postgresql.org/wiki/FAQ', permanent=True)),
	(r'^docs/faqs.FAQ_DEV.*', RedirectView.as_view(url='https://wiki.postgresql.org/wiki/Development_information', permanent=True)),
	(r'^docs/faqs.TODO.*', RedirectView.as_view(url='https://wiki.postgresql.org/wiki/Todo', permanent=True)),
	(r'^about/license/$', RedirectView.as_view(url='/about/licence', permanent=True)),

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

	# We use selectable only for /admin/ for now, so put it there to avoid caching issues
	(r'^admin/selectable/', include('selectable.urls')),

	# Uncomment the next line to enable the admin:
	(r'^admin/', include(admin.site.urls)),

	# This should not happen in production - serve by the webserver natively!
	url(r'^(favicon.ico)$', 'django.views.static.serve', {
		'document_root': 'media',
	}),

	# Crash testing URL :-)
	(r'^crashtest/$', 'pgweb.misc.views.crashtest'),

	# If we're getting an attempt for something ending in HTML, just get rid of it
	(r'^(.*)\.html$', 'pgweb.legacyurl.views.html_extension'),

	# Fallback for static pages, must be at the bottom
	(r'^(.*)/$', 'pgweb.core.views.fallback'),
)
