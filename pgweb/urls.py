from django.conf.urls import include, url
from django.views.generic import RedirectView

# Register our save signal handlers
from pgweb.util.signals import register_basic_signal_handlers
register_basic_signal_handlers()

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import pgweb.contributors.views
import pgweb.core.views
import pgweb.docs.views
import pgweb.downloads.views
import pgweb.events.views
import pgweb.featurematrix.views
import pgweb.legacyurl.views
import pgweb.lists.views
import pgweb.misc.views
import pgweb.news.views
import pgweb.profserv.views
import pgweb.pugs.views
import pgweb.search.views
import pgweb.security.views
import pgweb.sponsors.views
import pgweb.survey.views

from pgweb.core.feeds import VersionFeed
from pgweb.news.feeds import NewsFeed
from pgweb.events.feeds import EventFeed

urlpatterns = [
	url(r'^$', pgweb.core.views.home),
	url(r'^dyncss/(?P<css>base|docs).css$', pgweb.core.views.dynamic_css),

	url(r'^about/$', pgweb.core.views.about),
	url(r'^about/newsarchive/([^/]+/)?$', pgweb.news.views.archive),
	url(r'^about/news/(\d+)(-.*)?/$', pgweb.news.views.item),
	url(r'^about/news/taglist.json/$', pgweb.news.views.taglist_json),
	url(r'^about/events/$', pgweb.events.views.main),
	url(r'^about/eventarchive/$', pgweb.events.views.archive),
	url(r'^about/event/(\d+)(-.*)?/$', pgweb.events.views.item),
	url(r'^about/featurematrix/$', pgweb.featurematrix.views.root),
	url(r'^about/featurematrix/detail/(\d+)/$', pgweb.featurematrix.views.detail),

	url(r'^ftp/(.*/)?$', pgweb.downloads.views.ftpbrowser),
	url(r'^download/mirrors-ftp/+(.*)$', pgweb.downloads.views.mirrorselect),
	url(r'^download/product-categories/$', pgweb.downloads.views.categorylist),
	url(r'^download/products/(\d+)(-.*)?/$', pgweb.downloads.views.productlist),
	url(r'^applications-v2.xml$', pgweb.downloads.views.applications_v2_xml),
	url(r'^download/uploadftp/', pgweb.downloads.views.uploadftp),
	url(r'^download/uploadyum/', pgweb.downloads.views.uploadyum),
	url(r'^download/js/yum.js', pgweb.downloads.views.yum_js),

	url(r'^docs/$', pgweb.docs.views.root),
	url(r'^docs/manuals/$', pgweb.docs.views.manuals),
	url(r'^docs/manuals/archive/$', pgweb.docs.views.manualarchive),
	# Legacy URLs for accessing the docs page; provides a permanent redirect
	url(r'^docs/(current|devel|\d+(?:\.\d)?)/(static|interactive)/((.*).html?)?$', pgweb.docs.views.docspermanentredirect),
	url(r'^docs/(current|devel|\d+(?:\.\d)?)/(.*).html?$', pgweb.docs.views.docpage),
	url(r'^docs/(current|devel|\d+(?:\.\d)?)/$', pgweb.docs.views.docsrootpage),
	url(r'^docs/(current|devel|\d+(?:\.\d)?)/$', pgweb.docs.views.redirect_root),

	url(r'^community/$', pgweb.core.views.community),
	url(r'^community/contributors/$', pgweb.contributors.views.completelist),
	url(r'^community/lists/$', RedirectView.as_view(url='/list/', permanent=True)),
	url(r'^community/lists/subscribe/$', RedirectView.as_view(url='https://lists.postgresql.org/', permanent=True)),

	url(r'^community/lists/listinfo/$', pgweb.lists.views.listinfo),
	url(r'^community/survey/vote/(\d+)/$', pgweb.survey.views.vote),
	url(r'^community/survey[/\.](\d+)(-.*)?/$', pgweb.survey.views.results),
	url(r'^community/user-groups/$', pgweb.pugs.views.index),

	url(r'^search/$', pgweb.search.views.search),

	url(r'^support/security/$', pgweb.security.views.index),
	url(r'^support/security/(\d\.\d|\d{2})/$', pgweb.security.views.version),
	url(r'^support/security_archive/$', RedirectView.as_view(url='/support/security/', permanent=True)),

	url(r'^support/professional_(support|hosting)/$', pgweb.profserv.views.root),
	url(r'^support/professional_(support|hosting)[/_](.*)/$', pgweb.profserv.views.region),
	url(r'^account/submitbug/$', pgweb.misc.views.submitbug),
	url(r'^account/submitbug/(\d+)/$', pgweb.misc.views.submitbug_done),
	url(r'^support/submitbug/$', RedirectView.as_view(url='/account/submitbug/', permanent=True)),
	url(r'^support/versioning/$', pgweb.core.views.versions),
	url(r'^bugs_redir/(\d+)/$', pgweb.misc.views.bugs_redir),

	url(r'^about/sponsors/$', pgweb.sponsors.views.sponsors),
	url(r'^about/servers/$', pgweb.sponsors.views.servers),

	url(r'^robots.txt$', pgweb.core.views.robots),

	###
	# RSS feeds
	###
	url(r'^versions.rss$', VersionFeed()),
	url(r'^news(/(?P<tagurl>[^/]+))?.rss$', NewsFeed()),
	url(r'^events.rss$', EventFeed()),

	###
	# Special sections
	###
	url(r'^account/', include('pgweb.account.urls')),

	###
	# Sitemap (FIXME: support for >50k urls!)
	###
	url(r'^sitemap.xml', pgweb.core.views.sitemap),
	url(r'^sitemap_internal.xml', pgweb.core.views.sitemap_internal),

	###
	# Workaround for broken links pushed in press release
	###
	url(r'^downloads/$', RedirectView.as_view(url='/download/', permanent=True)),

	###
	# Legacy URLs from old structurs, but used in places like press releases
	# so needs to live a bit longer.
	###
	url(r'^about/press/contact/$', RedirectView.as_view(url='/about/press/', permanent=True)),

	###
	# Images that are used from other community sites
	###
	url(r'^layout/images/(?P<f>[a-z0-9_\.]+)$', RedirectView.as_view(url='/media/img/layout/%(f)s', permanent=True)),
	###
	# Handle redirect on incorrect spelling of licence
	###
	url(r'^about/license/$', RedirectView.as_view(url='/about/licence', permanent=True)),

	###
	# Links included in emails on the lists (do we need to check this for XSS?)
	###
	url(r'^mailpref/([a-z0-9_-]+)/$', pgweb.legacyurl.views.mailpref),

	# Some basic information about the connection (for debugging purposes)
	url(r'^system_information/$', pgweb.core.views.system_information),
	# Sync timestamp, for automirror
	url(r'^web_sync_timestamp$', pgweb.core.views.sync_timestamp),

	# API endpoints
	url(r'^api/varnish/purge/$', pgweb.core.views.api_varnish_purge),

	# Override some URLs in admin, to provide our own pages
	url(r'^admin/pending/$', pgweb.core.views.admin_pending),
	url(r'^admin/purge/$', pgweb.core.views.admin_purge),
	url(r'^admin/mergeorg/$', pgweb.core.views.admin_mergeorg),

	# We use selectable only for /admin/ for now, so put it there to avoid caching issues
	url(r'^admin/selectable/', include('selectable.urls')),

	# Uncomment the next line to enable the admin:
	url(r'^admin/', include(admin.site.urls)),

	# Crash testing URL :-)
	url(r'^crashtest/$', pgweb.misc.views.crashtest),

	# Fallback for static pages, must be at the bottom
	url(r'^(.*)/$', pgweb.core.views.fallback),
]
