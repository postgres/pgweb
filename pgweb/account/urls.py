from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r'^$', 'account.views.home'),
    
    # News & Events
    (r'^news/(.*)/$', 'news.views.form'),
    (r'^events/(.*)/$', 'events.views.form'),

    # Software catalogue
    (r'^organisations/(.*)/$', 'core.views.organisationform'),
    (r'^products/(.*)/$', 'downloads.views.productform'),

    # Docs comments
    (r'^comments/(new)/(.*)/(.*)/$', 'docs.views.commentform'),

    # Log in
    (r'^login/$', 'account.views.login'),

    # Log out
    (r'^logout/$', 'account.views.logout'),
)
