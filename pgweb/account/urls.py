from django.conf.urls.defaults import *
from django.contrib.auth.views import logout_then_login, login


urlpatterns = patterns('',
    (r'^$', 'account.views.home'),
    
    # News & Events
    (r'^news/(.*)/$', 'news.views.form'),
    (r'^events/(.*)/$', 'events.views.form'),

    # Log in
    (r'^login/$', login, {'template_name':'account/login.html'}),

    # Log out
    (r'^logout/$', logout_then_login, {'login_url': '/' }),
)
