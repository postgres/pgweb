from django.conf.urls import url
from django.conf import settings

import pgweb.account.views
import pgweb.account.oauthclient

pgweb.account.oauthclient.configure()

urlpatterns = [
    url(r'^$', pgweb.account.views.home),

    # Community authenticatoin
    url(r'^auth/(\d+)/$', pgweb.account.views.communityauth),
    url(r'^auth/(\d+)/logout/$', pgweb.account.views.communityauth_logout),
    url(r'^auth/(\d+)/consent/$', pgweb.account.views.communityauth_consent),
    url(r'^auth/(\d+)/search/$', pgweb.account.views.communityauth_search),
    url(r'^auth/(\d+)/getkeys/(\d+/)?$', pgweb.account.views.communityauth_getkeys),

    # Profile
    url(r'^profile/$', pgweb.account.views.profile),
    url(r'^profile/add_email/([0-9a-f]+)/$', pgweb.account.views.confirm_add_email),

    # List of items to edit
    url(r'^edit/(.*)/$', pgweb.account.views.listobjects),

    # Submitted items
    url(r'^(?P<objtype>news)/(?P<item>\d+)/(?P<what>submit|withdraw)/$', pgweb.account.views.submitted_item_submitwithdraw),
    url(r'^(?P<objtype>news|events|products|organisations|services)/(?P<item>\d+|new)/$', pgweb.account.views.submitted_item_form),
    url(r'^organisations/confirm/([0-9a-f]+)/$', pgweb.account.views.confirm_org_email),

    # Markdown preview (silly to have in /account/, but that's where all the markdown forms are so meh)
    url(r'^mdpreview/', pgweb.account.views.markdown_preview),

    # Organisation information
    url(r'^orglist/$', pgweb.account.views.orglist),

    # Docs comments
    url(r'^comments/(new)/([^/]+)/([^/]+)/$', pgweb.docs.views.commentform),
    url(r'^comments/(new)/([^/]+)/([^/]+)/done/$', pgweb.docs.views.commentform_done),

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

for provider in list(settings.OAUTH.keys()):
    urlpatterns.append(url(r'^login/({0})/$'.format(provider), pgweb.account.oauthclient.login_oauth))
