from django.conf.urls import include
from django.urls import path, re_path
from django.views.generic import RedirectView
from django.conf import settings

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
from pgweb.core.json import versions_json

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    re_path(r'^$', pgweb.core.views.home),
    re_path(r'^dyncss/(?P<css>base).css$', pgweb.core.views.dynamic_css),

    re_path(r'^about/$', pgweb.core.views.about),
    re_path(r'^about/newsarchive/(?P<tag>[^/]*/)?(?P<paginator>[0-9]{8}/)?$', pgweb.news.views.archive),
    re_path(r'^about/news/(?P<slug>[^/]+)-(?P<itemid>\d+)/$', pgweb.news.views.item),
    re_path(r'^about/news/(?P<itemid>\d+)(?P<slug>-.*)?/$', pgweb.news.views.item),
    re_path(r'^about/news/taglist.json/$', pgweb.news.views.taglist_json),
    re_path(r'^about/events/$', pgweb.events.views.main),
    re_path(r'^about/eventarchive/$', pgweb.events.views.archive),
    re_path(r'^about/event/(?P<itemid>\d+)(<?P<slug>-.*)?/$', pgweb.events.views.item),
    re_path(r'^about/event/(?P<slug>[^/]+)-(?P<itemid>\d+)/$', pgweb.events.views.item),
    re_path(r'^about/featurematrix/$', pgweb.featurematrix.views.root),
    re_path(r'^about/featurematrix/detail/(\d+)/$', pgweb.featurematrix.views.detail),
    re_path(r'^about/privacypolicy/$', RedirectView.as_view(url='/about/policies/privacy/', permanent=True)),

    re_path(r'^ftp/(.*/)?$', pgweb.downloads.views.ftpbrowser),
    re_path(r'^download/mirrors-ftp/+(.*)$', pgweb.downloads.views.mirrorselect),
    re_path(r'^download/product-categories/$', pgweb.downloads.views.categorylist),
    re_path(r'^download/products/(\d+)(-.*)?/$', pgweb.downloads.views.productlist),
    re_path(r'^applications-v2.xml$', pgweb.downloads.views.applications_v2_xml),
    re_path(r'^download/uploadftp/', pgweb.downloads.views.uploadftp),
    re_path(r'^download/uploadyum/', pgweb.downloads.views.uploadyum),
    re_path(r'^download/js/yum.js', pgweb.downloads.views.yum_js),

    re_path(r'^docs/$', pgweb.docs.views.root),
    re_path(r'^docs/manuals/$', pgweb.docs.views.manuals),
    re_path(r'^docs/manuals/archive/$', pgweb.docs.views.manualarchive),
    re_path(r'^docs/release/$', pgweb.docs.views.release_notes_list),
    re_path(r'^docs/release/(\d+(?:\.\d+){0,2})/$', pgweb.docs.views.release_notes),
    # Legacy URLs for accessing the docs page; provides a permanent redirect
    re_path(r'^docs/(current|devel|\d+(?:\.\d)?)/(static|interactive)/(([^/]+).html?)?$', pgweb.docs.views.docspermanentredirect),
    re_path(r'^docs/(current|devel|\d+(?:\.\d)?)/([^/]+).html?$', pgweb.docs.views.docpage),
    re_path(r'^docs/(current|devel|\d+(?:\.\d)?)/([^/]+).svg$', pgweb.docs.views.docsvg),
    re_path(r'^docs/(current|devel|\d+(?:\.\d)?)/$', pgweb.docs.views.docsrootpage),
    re_path(r'^docs/(current|devel|\d+(?:\.\d)?)/$', pgweb.docs.views.redirect_root),

    re_path(r'^community/$', pgweb.core.views.community),
    re_path(r'^community/contributors/$', pgweb.contributors.views.completelist),
    re_path(r'^community/lists/$', RedirectView.as_view(url='/list/', permanent=True)),
    re_path(r'^community/lists/subscribe/$', RedirectView.as_view(url='https://lists.postgresql.org/', permanent=True)),

    re_path(r'^community/lists/listinfo/$', pgweb.lists.views.listinfo),
    re_path(r'^community/recognition/$', RedirectView.as_view(url='/about/policies/', permanent=True)),
    re_path(r'^community/survey/vote/(\d+)/$', pgweb.survey.views.vote),
    re_path(r'^community/survey[/\.](\d+)(-.*)?/$', pgweb.survey.views.results),
    re_path(r'^community/user-groups/$', pgweb.pugs.views.index),

    re_path(r'^search/$', pgweb.search.views.search),

    re_path(r'^support/security/$', pgweb.security.views.index),
    re_path(r'^support/security/(\d\.\d|\d{2})/$', pgweb.security.views.version),
    re_path(r'^support/security/(?P<cve_prefix>CVE|cve)-(?P<cve>\d{4}-\d{4,7})/$', pgweb.security.views.details),
    re_path(r'^support/security_archive/$', RedirectView.as_view(url='/support/security/', permanent=True)),

    re_path(r'^support/professional_(support|hosting)/$', pgweb.profserv.views.root),
    re_path(r'^support/professional_(support|hosting)[/_](.*)/$', pgweb.profserv.views.region),
    re_path(r'^account/submitbug/$', pgweb.misc.views.submitbug),
    re_path(r'^account/submitbug/(\d+)/$', pgweb.misc.views.submitbug_done),
    re_path(r'^support/submitbug/$', RedirectView.as_view(url='/account/submitbug/', permanent=True)),
    re_path(r'^support/versioning/$', pgweb.core.views.versions),
    re_path(r'^bugs_redir/(\d+)/$', pgweb.misc.views.bugs_redir),

    re_path(r'^about/sponsors/$', pgweb.sponsors.views.sponsors),
    re_path(r'^about/contributing/$', pgweb.sponsors.views.contributing),
    re_path(r'^about/financial/$', pgweb.sponsors.views.financial),
    re_path(r'^about/servers/$', pgweb.sponsors.views.servers),

    re_path(r'^robots.txt$', pgweb.core.views.robots),

    ###
    # RSS feeds
    ###
    re_path(r'^versions.rss$', VersionFeed()),
    re_path(r'^news(/(?P<tagurl>[^/]+))?.rss$', NewsFeed()),
    re_path(r'^events.rss$', EventFeed()),

    ###
    # JSON feeds
    ###
    re_path(r'^versions.json$', versions_json),

    ###
    # Special sections
    ###
    re_path(r'^account/', include('pgweb.account.urls')),

    ###
    # Sitemap (FIXME: support for >50k urls!)
    ###
    re_path(r'^sitemap.xml', pgweb.core.views.sitemap),
    re_path(r'^sitemap_internal.xml', pgweb.core.views.sitemap_internal),

    ###
    # Workaround for broken links pushed in press release
    ###
    re_path(r'^downloads/$', RedirectView.as_view(url='/download/', permanent=True)),

    ###
    # Legacy URLs from old structurs, but used in places like press releases
    # so needs to live a bit longer.
    ###
    re_path(r'^about/press/contact/$', RedirectView.as_view(url='/about/press/', permanent=True)),

    ###
    # Images that are used from other community sites
    ###
    re_path(r'^layout/images/(?P<f>[a-z0-9_\.]+)$', RedirectView.as_view(url='/media/img/layout/%(f)s', permanent=True)),
    ###
    # Handle redirect on incorrect spelling of licence
    ###
    re_path(r'^about/license/$', RedirectView.as_view(url='/about/licence', permanent=True)),

    ###
    # Links included in emails on the lists (do we need to check this for XSS?)
    ###
    re_path(r'^mailpref/([a-z0-9_-]+)/$', pgweb.legacyurl.views.mailpref),

    # Some basic information about the connection (for debugging purposes)
    re_path(r'^system_information/$', pgweb.core.views.system_information),
    # Sync timestamp, for automirror
    re_path(r'^web_sync_timestamp$', pgweb.core.views.sync_timestamp),

    # API endpoints
    re_path(r'^api/varnish/purge/$', pgweb.core.views.api_varnish_purge),

    # Override some URLs in admin, to provide our own pages
    re_path(r'^admin/pending/$', pgweb.core.views.admin_pending),
    re_path(r'^admin/purge/$', pgweb.core.views.admin_purge),
    re_path(r'^admin/mergeorg/$', pgweb.core.views.admin_mergeorg),
    re_path(r'^admin/_moderate/(\w+)/(\d+)/$', pgweb.core.views.admin_moderate),
    re_path(r'^admin/auth/user/(\d+)/change/resetpassword/$', pgweb.core.views.admin_resetpassword),

    # Uncomment the next line to enable the admin:
    re_path(r'^admin/', admin.site.urls),

    # Crash testing URL :-)
    re_path(r'^crashtest/$', pgweb.misc.views.crashtest),

    # Fallback for static pages, must be at the bottom
    re_path(r'^(.*)/$', pgweb.core.views.fallback),
]


if settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
