from django.urls import re_path
from django.conf import settings

import pgweb.account.views
import pgweb.account.oauthclient

pgweb.account.oauthclient.configure()

urlpatterns = [
    re_path(r'^$', pgweb.account.views.home),

    # Community authenticatoin
    re_path(r'^auth/(\d+)/$', pgweb.account.views.communityauth),
    re_path(r'^auth/(\d+)/logout/$', pgweb.account.views.communityauth_logout),
    re_path(r'^auth/(\d+)/consent/$', pgweb.account.views.communityauth_consent),
    re_path(r'^auth/(\d+)/search/$', pgweb.account.views.communityauth_search),
    re_path(r'^auth/(\d+)/getkeys/(\d+/)?$', pgweb.account.views.communityauth_getkeys),
    re_path(r'^auth/(\d+)/subscribe/$', pgweb.account.views.communityauth_subscribe),

    # Profile
    re_path(r'^profile/$', pgweb.account.views.profile),
    re_path(r'^profile/add_email/([0-9a-f]+)/$', pgweb.account.views.confirm_add_email),

    # List of items to edit
    re_path(r'^edit/(.*)/$', pgweb.account.views.listobjects),

    # Submitted items
    re_path(r'^(?P<objtype>news)/(?P<item>\d+)/(?P<what>submit|withdraw)/$', pgweb.account.views.submitted_item_submitwithdraw),
    re_path(r'^(?P<objtype>news|events|products|organisations|services)/(?P<item>\d+|new)/$', pgweb.account.views.submitted_item_form),
    re_path(r'^organisations/confirm/([0-9a-f]+)/$', pgweb.account.views.confirm_org_email),

    # Markdown preview (silly to have in /account/, but that's where all the markdown forms are so meh)
    re_path(r'^mdpreview/', pgweb.account.views.markdown_preview),

    # Organisation information
    re_path(r'^orglist/$', pgweb.account.views.orglist),

    # Docs comments
    re_path(r'^comments/(new)/([^/]+)/([^/]+)/$', pgweb.docs.views.commentform),
    re_path(r'^comments/(new)/([^/]+)/([^/]+)/done/$', pgweb.docs.views.commentform_done),

    # Log in, logout, change password etc
    re_path(r'^login/$', pgweb.account.views.login),
    re_path(r'^logout/$', pgweb.account.views.logout),
    re_path(r'^changepwd/$', pgweb.account.views.changepwd),
    re_path(r'^changepwd/done/$', pgweb.account.views.change_done),
    re_path(r'^reset/$', pgweb.account.views.resetpwd),
    re_path(r'^reset/done/$', pgweb.account.views.reset_done),
    re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)-(?P<token>[0-9A-Za-z]+-[0-9A-Za-z]+)/$', pgweb.account.views.reset_confirm),
    re_path(r'^reset/complete/$', pgweb.account.views.reset_complete),
    re_path(r'^signup/$', pgweb.account.views.signup),
    re_path(r'^signup/complete/$', pgweb.account.views.signup_complete),
    re_path(r'^signup/oauth/$', pgweb.account.views.signup_oauth),
]

for provider in list(settings.OAUTH.keys()):
    urlpatterns.append(re_path(r'^login/({0})/$'.format(provider), pgweb.account.oauthclient.login_oauth))
