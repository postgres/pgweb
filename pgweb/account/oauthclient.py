from django.conf import settings
from django.contrib.auth import login as django_login
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User

import sys

from pgweb.util.misc import get_client_ip

import logging
log = logging.getLogger(__name__)

#
# Generic OAuth login for multiple providers
#
def _login_oauth(request, provider, authurl, tokenurl, scope, authdatafunc):
	from requests_oauthlib import OAuth2Session

	client_id = settings.OAUTH[provider]['clientid']
	client_secret = settings.OAUTH[provider]['secret']
	redir = '{0}/account/login/{1}/'.format(settings.SITE_ROOT, provider)

	oa = OAuth2Session(client_id, scope=scope, redirect_uri=redir)
	if request.GET.has_key('code'):
		log.info("Completing {0} oauth2 step from {1}".format(provider, get_client_ip(request)))

		# Receiving a login request from the provider, so validate data
		# and log the user in.
		if request.GET['state'] != request.session.pop('oauth_state'):
			log.warning("Invalid state received in {0} oauth2 step from {1}".format(provider, get_client_ip(request)))
			raise Exception("Invalid OAuth state received")

		token = oa.fetch_token(tokenurl,
							   client_secret=client_secret,
							   code=request.GET['code'])
		(email, firstname, lastname) = authdatafunc(oa)

		try:
			user = User.objects.get(email=email)
		except User.DoesNotExist:
			log.info("Oauth signin of {0} using {1} from {2}. User not found, offering signup.".format(email, provider, get_client_ip(request)))

			# Offer the user a chance to sign up. The full flow is
			# handled elsewhere, so store the details we got from
			# the oauth login in the session, and pass the user on.
			request.session['oauth_email'] = email
			request.session['oauth_firstname'] = firstname
			request.session['oauth_lastname'] = lastname
			return HttpResponseRedirect('/account/signup/oauth/')

		log.info("Oauth signin of {0} using {1} from {2}.".format(email, provider, get_client_ip(request)))

		user.backend = settings.AUTHENTICATION_BACKENDS[0]
		django_login(request, user)
		n = request.session.pop('login_next')
		if n:
			return HttpResponseRedirect(n)
		else:
			return HttpResponseRedirect('/account/')
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
# Google login
#  Registration: https://console.developers.google.com/apis/
#
def oauth_login_google(request):
	def _google_auth_data(oa):
		r = oa.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
		if not r['verified_email']:
			raise Exception("Verified email required")
		return (r['email'],
				r['given_name'],
				r['family_name'])

	return _login_oauth(
		request,
		'google',
		'https://accounts.google.com/o/oauth2/v2/auth',
		'https://accounts.google.com/o/oauth2/token',
		['https://www.googleapis.com/auth/userinfo.email',
			 'https://www.googleapis.com/auth/userinfo.profile'],
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
		n = r['name'].split(None, 1)
		# Email is at a separate endpoint
		r = oa.get('https://api.github.com/user/emails').json()
		for e in r:
			if e['verified'] and e['primary']:
				return (
					e['email'],
					n[0],
					n[1],
				)
		raise Exception("Could not find email")

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
		return (r['email'],
				r['first_name'],
				r['last_name'])

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
		return (r['emails']['account'],
				r['first_name'],
				r['last_name'])

	return _login_oauth(
		request,
		'microsoft',
		'https://login.live.com/oauth20_authorize.srf',
		'https://login.live.com/oauth20_token.srf',
		['wl.basic', 'wl.emails' ],
		_microsoft_auth_data)


def login_oauth(request, provider):
	fn = 'oauth_login_{0}'.format(provider)
	m = sys.modules[__name__]
	if hasattr(m, fn):
		return getattr(m, fn)(request)
