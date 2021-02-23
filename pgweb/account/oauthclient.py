from django.conf import settings
from django.contrib.auth import login as django_login
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User

import os
import sys

from pgweb.util.misc import get_client_ip
from pgweb.util.decorators import queryparams
from pgweb.core.models import UserProfile

import logging
log = logging.getLogger(__name__)


class OAuthException(Exception):
    pass


#
# Disable scope validation in oauthlib, as it throws an exception we cannot
# recover from. Manual check that turns it into a warning below.
#
def configure():
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


def _perform_oauth_login(request, provider, email, firstname, lastname):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        log.info("Oauth signin of {0} using {1} from {2}. User not found, offering signup.".format(email, provider, get_client_ip(request)))

        # Offer the user a chance to sign up. The full flow is
        # handled elsewhere, so store the details we got from
        # the oauth login in the session, and pass the user on.
        request.session['oauth_email'] = email
        request.session['oauth_firstname'] = firstname or ''
        request.session['oauth_lastname'] = lastname or ''
        return HttpResponseRedirect('/account/signup/oauth/')

    log.info("Oauth signin of {0} using {1} from {2}.".format(email, provider, get_client_ip(request)))
    if UserProfile.objects.filter(user=user).exists():
        if UserProfile.objects.get(user=user).block_oauth:
            log.warning("Account {0} ({1}) is blocked from OAuth login".format(user.username, email))
            return HttpResponse("OAuth login not allowed to this account.")

    user.backend = settings.AUTHENTICATION_BACKENDS[0]
    django_login(request, user)
    n = request.session.pop('login_next')
    if n:
        return HttpResponseRedirect(n)
    else:
        return HttpResponseRedirect('/account/')


#
# Generic OAuth2 login for multiple providers
#
def _login_oauth(request, provider, authurl, tokenurl, scope, authdatafunc):
    from requests_oauthlib import OAuth2Session

    client_id = settings.OAUTH[provider]['clientid']
    client_secret = settings.OAUTH[provider]['secret']
    redir = '{0}/account/login/{1}/'.format(settings.SITE_ROOT, provider)

    oa = OAuth2Session(client_id, scope=scope, redirect_uri=redir)
    if 'code' in request.GET:
        log.info("Completing {0} oauth2 step from {1}".format(provider, get_client_ip(request)))

        # Receiving a login request from the provider, so validate data
        # and log the user in.
        if request.GET.get('state', '') != request.session.pop('oauth_state'):
            log.warning("Invalid state received in {0} oauth2 step from {1}".format(provider, get_client_ip(request)))
            raise OAuthException("Invalid OAuth state received")

        token = oa.fetch_token(tokenurl,
                               client_secret=client_secret,
                               code=request.GET['code'])
        if token.scope_changed:
            log.warning("Oauth scope changed for {0} login from '{1}' to '{2}'".format(provider, token.old_scope, token.scope))

        try:
            (email, firstname, lastname) = authdatafunc(oa)
            email = email.lower()
        except KeyError as e:
            log.warning("Oauth signing using {0} was missing data: {1}".format(provider, e))
            return HttpResponse('OAuth login was missing critical data. To log in, you need to allow access to email, first name and last name!')

        return _perform_oauth_login(request, provider, email, firstname, lastname)
    else:
        log.info("Initiating {0} oauth2 step from {1}".format(provider, get_client_ip(request)))
        # First step is redirect to provider
        authorization_url, state = oa.authorization_url(
            authurl,
            prompt='consent',
        )
        request.session['login_next'] = request.GET.get('next', '')
        request.session['oauth_state'] = state
        request.session.modified = True
        return HttpResponseRedirect(authorization_url)


#
# Generic Oauth1 provider
#
def _login_oauth1(request, provider, requesturl, accessurl, baseauthurl, authdatafunc):
    from requests_oauthlib import OAuth1Session

    client_id = settings.OAUTH[provider]['clientid']
    client_secret = settings.OAUTH[provider]['secret']
    redir = '{0}/account/login/{1}/'.format(settings.SITE_ROOT, provider)

    if 'oauth_verifier' in request.GET:
        log.info("Completing {0} oauth1 step from {1}".format(provider, get_client_ip(request)))

        oa = OAuth1Session(client_id, client_secret)
        r = oa.parse_authorization_response(request.build_absolute_uri())
        verifier = r.get('oauth_verifier')

        ro_key = request.session.pop('ro_key')
        ro_secret = request.session.pop('ro_secret')

        oa = OAuth1Session(client_id, client_secret, ro_key, ro_secret, verifier=verifier)
        tokens = oa.fetch_access_token(accessurl)

        try:
            (email, firstname, lastname) = authdatafunc(oa)
            email = email.lower()
        except KeyError as e:
            log.warning("Oauth1 signing using {0} was missing data: {1}".format(provider, e))
            return HttpResponse('OAuth login was missing critical data. To log in, you need to allow access to email, first name and last name!')

        return _perform_oauth_login(request, provider, email, firstname, lastname)
    else:
        log.info("Initiating {0} oauth1 step from {1}".format(provider, get_client_ip(request)))

        oa = OAuth1Session(client_id, client_secret=client_secret)
        fr = oa.fetch_request_token(requesturl)
        authorization_url = oa.authorization_url(baseauthurl)

        request.session['login_next'] = request.GET.get('next', '')
        request.session['ro_key'] = fr.get('oauth_token')
        request.session['ro_secret'] = fr.get('oauth_token_secret')
        request.session.modified = True
        return HttpResponseRedirect(authorization_url)


#
# Google login
#  Registration: https://console.developers.google.com/apis/
#
def oauth_login_google(request):
    def _google_auth_data(oa):
        r = oa.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
        if not r['verified_email']:
            raise OAuthException("The email in your google profile must be verified in order to log in")
        return (r['email'],
                r.get('given_name', ''),
                r.get('family_name', ''))

    return _login_oauth(
        request,
        'google',
        'https://accounts.google.com/o/oauth2/v2/auth',
        'https://accounts.google.com/o/oauth2/token',
        [
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ],
        _google_auth_data)


#
# Github login
#  Registration: https://github.com/settings/developers
#
def oauth_login_github(request):
    def _github_auth_data(oa):
        # Github just returns full name, so we're just going to have to
        # split that.
        r = oa.get('https://api.github.com/user').json()
        if 'name' in r and r['name']:
            n = r['name'].split(None, 1)
            # Some accounts only have one name, extend with an empty
            # lastname, so the user can fill it out manually.
            while len(n) < 2:
                n.append('')
        else:
            # Some github accounts have no name on them, so we can just
            # let the user fill it out manually in that case.
            n = ['', '']
        # Email is at a separate endpoint
        r = oa.get('https://api.github.com/user/emails').json()
        for e in r:
            if e['verified'] and e['primary']:
                return (
                    e['email'],
                    n[0],
                    n[1],
                )
        raise OAuthException("Your GitHub profile must include a verified email address in order to log in")

    return _login_oauth(
        request,
        'github',
        'https://github.com/login/oauth/authorize',
        'https://github.com/login/oauth/access_token',
        ['user:email', ],
        _github_auth_data)


#
# Facebook login
#  Registration: https://developers.facebook.com/apps
#
def oauth_login_facebook(request):
    def _facebook_auth_data(oa):
        r = oa.get('https://graph.facebook.com/me?fields=email,first_name,last_name').json()
        if 'email' not in r:
            raise OAuthException("Your Facebook profile must provide an email address in order to log in")

        return (r['email'],
                r.get('first_name', ''),
                r.get('last_name', ''))

    return _login_oauth(
        request,
        'facebook',
        'https://www.facebook.com/dialog/oauth',
        'https://graph.facebook.com/oauth/access_token',
        ['public_profile', 'email', ],
        _facebook_auth_data)


#
# Microsoft login
#  Registration: https://apps.dev.microsoft.com/
#
def oauth_login_microsoft(request):
    def _microsoft_auth_data(oa):
        r = oa.get("https://apis.live.net/v5.0/me").json()
        if 'emails' not in r or 'account' not in r['emails']:
            raise OAuthException("Your MicrosoftFacebook profile must provide an email address in order to log in")

        return (r['emails']['account'],
                r.get('first_name', ''),
                r.get('last_name', ''))

    return _login_oauth(
        request,
        'microsoft',
        'https://login.live.com/oauth20_authorize.srf',
        'https://login.live.com/oauth20_token.srf',
        ['wl.basic', 'wl.emails', ],
        _microsoft_auth_data)


#
# Twitter login
#  Registration: https://developer.twitter.com/en/apps
#
def oauth_login_twitter(request):
    def _twitter_auth_data(oa):
        r = oa.get('https://api.twitter.com/1.1/account/verify_credentials.json?include_email=true').json()
        n = r['name'].split(None, 1)
        while len(n) < 2:
            # Handle single name names
            n.append('')

        return (
            r['email'],
            n[0],
            n[1]
        )

    return _login_oauth1(
        request,
        'twitter',
        'https://api.twitter.com/oauth/request_token',
        'https://api.twitter.com/oauth/access_token',
        'https://api.twitter.com/oauth/authorize',
        _twitter_auth_data)


@queryparams('code', 'state', 'next')
def login_oauth(request, provider):
    fn = 'oauth_login_{0}'.format(provider)
    m = sys.modules[__name__]
    if hasattr(m, fn):
        try:
            return getattr(m, fn)(request)
        except OAuthException as e:
            return HttpResponse(e)
        except Exception as e:
            log.error('Exception during OAuth: %s' % e)
            return HttpResponse('An unhandled exception occurred during the authentication process')
