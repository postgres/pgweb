from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r'^$', 'account.views.home'),

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

    # Docs comments
    (r'^comments/(new)/(.*)/(.*)/$', 'docs.views.commentform'),

    # Log in, logout, change password etc
    (r'^login/$', 'account.views.login'),
    (r'^logout/$', 'account.views.logout'),
	(r'^changepwd/$', 'account.views.changepwd'),
	(r'^changepwd/done/$', 'django.contrib.auth.views.password_change_done', {
			'template_name': 'account/password_change_done.html', }),
	(r'^reset/$', 'account.views.resetpwd'),
	(r'^reset/done/$', 'django.contrib.auth.views.password_reset_done', {
			'template_name': 'account/password_reset_done.html', }),
	(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', {
			'template_name': 'account/password_reset_confirm.html', }),
	(r'^reset/complete/$', 'django.contrib.auth.views.password_reset_complete', {
			'template_name': 'account/password_reset_complete.html', }),
	(r'^signup/$', 'account.views.signup'),
	(r'^signup/complete/$', 'account.views.signup_complete'),
)
