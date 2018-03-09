from django.conf.urls import url
from django.conf import settings

import pgweb.account.views

urlpatterns = [
	url(r'^$', pgweb.account.views.home),

	# Community authenticatoin
	url(r'^auth/(\d+)/$', pgweb.account.views.communityauth),
	url(r'^auth/(\d+)/logout/$', pgweb.account.views.communityauth_logout),
	url(r'^auth/(\d+)/search/$', pgweb.account.views.communityauth_search),
	url(r'^auth/(\d+)/getkeys/(\d+/)?$', pgweb.account.views.communityauth_getkeys),

	# Profile
	url(r'^profile/$', pgweb.account.views.profile),
	url(r'^profile/change_email/$', pgweb.account.views.change_email),
	url(r'^profile/change_email/([0-9a-f]+)/$', pgweb.account.views.confirm_change_email),

	# List of items to edit
	url(r'^edit/(.*)/$', pgweb.account.views.listobjects),

	# News & Events
	url(r'^news/(.*)/$', pgweb.news.views.form),
	url(r'^events/(.*)/$', pgweb.events.views.form),

	# Software catalogue
	url(r'^organisations/(.*)/$', pgweb.core.views.organisationform),
	url(r'^products/(.*)/$', pgweb.downloads.views.productform),

	# Organisation information
	url(r'^orglist/$', pgweb.account.views.orglist),

	# Professional services
	url(r'^services/(.*)/$', pgweb.profserv.views.profservform),

	# Docs comments
	url(r'^comments/(new)/(.*)/(.*)/$', pgweb.docs.views.commentform),

	# Log in, logout, change password etc
	url(r'^login/$', pgweb.account.views.login),
	url(r'^logout/$', pgweb.account.views.logout),
	url(r'^changepwd/$', pgweb.account.views.changepwd),
	url(r'^changepwd/done/$', pgweb.account.views.change_done),
	url(r'^reset/$', pgweb.account.views.resetpwd),
	url(r'^reset/done/$', pgweb.account.views.reset_done),
	url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', pgweb.account.views.reset_confirm),
	url(r'^reset/complete/$', pgweb.account.views.reset_complete),
	url(r'^signup/$', pgweb.account.views.signup),
	url(r'^signup/complete/$', pgweb.account.views.signup_complete),
	url(r'^signup/oauth/$', pgweb.account.views.signup_oauth),
]

for provider in settings.OAUTH.keys():
	urlpatterns.append(url(r'^login/({0})/$'.format(provider), 'pgweb.account.oauthclient.login_oauth'))
