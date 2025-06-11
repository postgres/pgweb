from django.conf import settings
from django.contrib.auth import login as django_login
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

import base64
import hashlib
import json
import os
import sys
import time
import urllib.parse
from Cryptodome import Random
from Cryptodome.Cipher import AES

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


_cookie_key = hashlib.sha512(settings.SECRET_KEY.encode()).digest()


def set_encrypted_oauth_cookie_on(response, cookiecontent, path=None):
    cookiecontent['_ts'] = time.time()
    cookiedata = json.dumps(cookiecontent)
    r = Random.new()
    nonce = r.read(16)
    encryptor = AES.new(_cookie_key, AES.MODE_SIV, nonce=nonce)
    cipher, tag = encryptor.encrypt_and_digest(cookiedata.encode('ascii'))
    response.set_cookie(
        'pgweb_oauth',
        urllib.parse.urlencode({
            'n': base64.urlsafe_b64encode(nonce),
            'c': base64.urlsafe_b64encode(cipher),
            't': base64.urlsafe_b64encode(tag),
        }),
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        path=path or '/account/login/',
    )
    return response


def get_encrypted_oauth_cookie(request):
    if 'pgweb_oauth' not in request.COOKIES:
        raise OAuthException("Secure cookie missing")

    parts = urllib.parse.parse_qs(request.COOKIES['pgweb_oauth'])

    decryptor = AES.new(
        _cookie_key,
        AES.MODE_SIV,
        base64.urlsafe_b64decode(parts['n'][0]),
    )
    s = decryptor.decrypt_and_verify(
        base64.urlsafe_b64decode(parts['c'][0]),
        base64.urlsafe_b64decode(parts['t'][0]),
    )

    d = json.loads(s)
    if time.time() - d['_ts'] > 10 * 60:
        # 10 minutes to complete oauth login
        raise OAuthException("Cookie expired")
    del d['_ts']

    return d


def delete_encrypted_oauth_cookie_on(response):
    response.delete_cookie('pgweb_oauth')
    return response


def _perform_oauth_login(request, provider, email, firstname, lastname, nexturl):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        log.info("Oauth signin of {0} using {1} from {2}. User not found, offering signup.".format(email, provider, get_client_ip(request)))

        # Offer the user a chance to sign up. The full flow is
        # handled elsewhere, so store the details we got from
        # the oauth login in a secure cookie, and pass the user on.
        return set_encrypted_oauth_cookie_on(HttpResponseRedirect('/account/signup/oauth/'), {
            'oauth_email': email,
            'oauth_firstname': firstname or '',
            'oauth_lastname': lastname or '',
        }, '/account/signup/oauth/')

    log.info("Oauth signin of {0} using {1} from {2}.".format(email, provider, get_client_ip(request)))
    if UserProfile.objects.filter(user=user).exists():
        if UserProfile.objects.get(user=user).block_oauth:
            log.warning("Account {0} ({1}) is blocked from OAuth login".format(user.username, email))
            return HttpResponse("OAuth login not allowed to this account.")

    user.backend = settings.AUTHENTICATION_BACKENDS[0]
    django_login(request, user)
    return delete_encrypted_oauth_cookie_on(HttpResponseRedirect(nexturl or '/account/'))


#
# Generic OAuth2 login for multiple providers
#
def _login_oauth(request, provider, authurl, tokenurl, scope, authdatafunc):
    from requests_oauthlib import OAuth2Session

    client_id = settings.OAUTH[provider]['clientid']
    client_secret = settings.OAUTH[provider]['secret']
    redir = '{0}/account/login/{1}/'.format(settings.SITE_ROOT, provider)

    oa = OAuth2Session(client_id, scope=scope, redirect_uri=redir)
    if request.method == 'GET':
        if 'code' not in request.GET:
            raise OAuthException("No code provided")

        log.info("Completing {0} oauth2 step from {1}".format(provider, get_client_ip(request)))

        # Receiving a login request from the provider, so validate data
        # and log the user in.
        oauthdata = get_encrypted_oauth_cookie(request)

        if request.GET.get('state', '') != oauthdata['oauth_state']:
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

        return _perform_oauth_login(request, provider, email, firstname, lastname, oauthdata['next'])
    else:
        log.info("Initiating {0} oauth2 step from {1}".format(provider, get_client_ip(request)))
        # First step is redirect to provider
        authorization_url, state = oa.authorization_url(
            authurl,
            prompt='consent',
        )
        return set_encrypted_oauth_cookie_on(HttpResponseRedirect(authorization_url), {
            'next': request.POST.get('next', ''),
            'oauth_state': state,
        })


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

        oauthdata = get_encrypted_oauth_cookie(request)

        ro_key = oauthdata['ro_key']
        ro_secret = oauthdata['ro_secret']

        oa = OAuth1Session(client_id, client_secret, ro_key, ro_secret, verifier=verifier)
        tokens = oa.fetch_access_token(accessurl)

        try:
            (email, firstname, lastname) = authdatafunc(oa)
            email = email.lower()
        except KeyError as e:
            log.warning("Oauth1 signing using {0} was missing data: {1}".format(provider, e))
            return HttpResponse('OAuth login was missing critical data. To log in, you need to allow access to email, first name and last name!')

        return _perform_oauth_login(request, provider, email, firstname, lastname, oauthdata['next'])
    else:
        log.info("Initiating {0} oauth1 step from {1}".format(provider, get_client_ip(request)))

        oa = OAuth1Session(client_id, client_secret=client_secret)
        fr = oa.fetch_request_token(requesturl)
        authorization_url = oa.authorization_url(baseauthurl)

        return set_encrypted_oauth_cookie_on(HttpResponseRedirect(authorization_url), {
            'next': request.POST.get('next', ''),
            'ro_key': fr.get('oauth_token'),
            'ro_secret': fr.get('oauth_token_secret'),
        })


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


@require_POST
@csrf_exempt
def initiate_oauth_login(request):
    if 'submit' not in request.POST:
        return HttpResponse("Invalid post", status=400)
    return _oauth_login_dispatch(request.POST['submit'], request)


@require_GET
@queryparams('code', 'state', 'next', 'oauth_verifier')
def login_oauth(request, provider):
    return _oauth_login_dispatch(provider, request)


def _oauth_login_dispatch(provider, request):
    fn = 'oauth_login_{0}'.format(provider)
    m = sys.modules[__name__]
    if hasattr(m, fn):
        try:
            return getattr(m, fn)(request)
        except OAuthException as e:
            return HttpResponse(e, status=400)
        except Exception as e:
            log.error('Exception during OAuth: {}'.format(e))
            return HttpResponse('An unhandled exception occurred during the authentication process')
    else:
        raise Http404()
