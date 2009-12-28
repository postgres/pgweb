from django.conf.urls.defaults import *

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
feeds = {
	'versions': VersionFeed,
	'news': NewsFeed,
	'events': EventFeed,
}

urlpatterns = patterns('',
    (r'^$', 'pgweb.core.views.home'),

    (r'^about/newsarchive/$', 'news.views.archive'),
    (r'^about/news/(\d+)(-.*)?/$', 'news.views.item'),
    (r'^about/eventarchive/$', 'events.views.archive'),
    (r'^about/event/(\d+)(-.*)?/$', 'events.views.item'),
    (r'^about/quotesarchive/$', 'quotes.views.allquotes'),
    
    (r'^ftp/(.*/)?$', 'downloads.views.ftpbrowser'),
    (r'^download/product-categories/$', 'downloads.views.categorylist'),
    (r'^download/products/(\d+)(-.*)?/$', 'downloads.views.productlist'),

    (r'^docs/(current|\d\.\d)/(static|interactive)/(.*).html$', 'docs.views.docpage'),

    (r'^community/$', 'core.views.community'),
    (r'^community/contributors/$', 'contributors.views.completelist'),
    (r'^community/lists/$', 'lists.views.root'),
    (r'^community/lists/subscribe/$', 'lists.views.subscribe'),
    (r'^community/survey/vote/(\d+)/$', 'survey.views.vote'),
    (r'^community/survey[/\.](\d+)(-.*)?/$', 'survey.views.results'),

    (r'^support/professional_(support|hosting)/$', 'profserv.views.root'),
    (r'^support/professional_(support|hosting)[/_](.*)/$', 'profserv.views.region'),

    (r'about/sponsors/$', 'pgweb.sponsors.views.sponsors'),
    (r'about/servers/$', 'pgweb.sponsors.views.servers'),
    
    ###
    # RSS feeds
    ###
    (r'^(versions|news|events).rss$', 'django.contrib.syndication.views.feed', {'feed_dict':feeds}),

    ###
    # Special secttions
    ###
    (r'account/', include('account.urls')),
    
    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    # This should not happen in production - serve by the webserver natively!
    url(r'^media/(.*)$', 'django.views.static.serve', {
        'document_root': '../media',
    }),
    url(r'^(favicon.ico)$', 'django.views.static.serve', {
        'document_root': '../media',
    }),

    # Fallback for static pages, must be at the bottom
    (r'^(.*)/$', 'pgweb.core.views.fallback'),
)

