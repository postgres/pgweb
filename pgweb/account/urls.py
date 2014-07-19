from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r'^$', 'account.views.home'),

    # Community authenticatoin
    (r'^auth/(\d+)/$', 'account.views.communityauth'),
    (r'^auth/(\d+)/logout/$', 'account.views.communityauth_logout'),
    (r'^auth/(\d+)/search/$', 'account.views.communityauth_search'),

	# Profile
	(r'^profile/$', 'account.views.profile'),
    # List of items to edit
    (r'^edit/(.*)/$', 'account.views.listobjects'),

    # News & Events
    (r'^news/(.*)/$', 'news.views.form'),
    (r'^events/(.*)/$', 'events.views.form'),

    # Software catalogue
    (r'^organisations/(.*)/$', 'core.views.organisationform'),
    (r'^products/(.*)/$', 'downloads.views.productform'),

    # Organisation information
	(r'^orglist/$', 'account.views.orglist'),

    # Professional services
    (r'^services/(.*)/$', 'profserv.views.profservform'),

    # Docs comments
    (r'^comments/(new)/(.*)/(.*)/$', 'docs.views.commentform'),

    # Log in, logout, change password etc
    (r'^login/$', 'account.views.login'),
    (r'^logout/$', 'account.views.logout'),
	(r'^changepwd/$', 'account.views.changepwd'),
	(r'^changepwd/done/$', 'account.views.change_done'),
	(r'^reset/$', 'account.views.resetpwd'),
	(r'^reset/done/$', 'account.views.reset_done'),
	(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'account.views.reset_confirm'),
	(r'^reset/complete/$', 'account.views.reset_complete'),
	(r'^signup/$', 'account.views.signup'),
	(r'^signup/complete/$', 'account.views.signup_complete'),
)
