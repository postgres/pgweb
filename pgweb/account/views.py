from django.contrib.auth.models import User
from django.contrib.auth import login as django_login
import django.contrib.auth.views as authviews
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from pgweb.util.decorators import login_required
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import logout as django_logout
from django.conf import settings
from django.db import transaction
from django.db.models import Q

import base64
import urllib
from Crypto.Cipher import AES
from Crypto import Random
import time
import json
from datetime import datetime, timedelta
import itertools

from pgweb.util.contexts import NavContext
from pgweb.util.misc import send_template_mail, generate_random_token, get_client_ip
from pgweb.util.helpers import HttpServerError

from pgweb.news.models import NewsArticle
from pgweb.events.models import Event
from pgweb.core.models import Organisation, UserProfile
from pgweb.contributors.models import Contributor
from pgweb.downloads.models import Product
from pgweb.profserv.models import ProfessionalService

from models import CommunityAuthSite, EmailChangeToken
from forms import PgwebAuthenticationForm
from forms import SignupForm, SignupOauthForm
from forms import UserForm, UserProfileForm, ContributorForm
from forms import ChangeEmailForm

import logging
log = logging.getLogger(__name__)

# The value we store in user.password for oauth logins. This is
# a value that must not match any hashers.
OAUTH_PASSWORD_STORE='oauth_signin_account_no_password'

@login_required
def home(request):
	myarticles = NewsArticle.objects.filter(org__managers=request.user, approved=False)
	myevents = Event.objects.filter(org__managers=request.user, approved=False)
	myorgs = Organisation.objects.filter(managers=request.user, approved=False)
	myproducts = Product.objects.filter(org__managers=request.user, approved=False)
	myprofservs = ProfessionalService.objects.filter(org__managers=request.user, approved=False)
	return render_to_response('account/index.html', {
		'newsarticles': myarticles,
		'events': myevents,
		'organisations': myorgs,
		'products': myproducts,
		'profservs': myprofservs,
	}, NavContext(request, 'account'))

objtypes = {
	'news': {
		'title': 'News article',
		'objects': lambda u: NewsArticle.objects.filter(org__managers=u),
	},
	'events': {
		'title': 'Event',
		'objects': lambda u: Event.objects.filter(org__managers=u),
    },
	'products': {
		'title': 'Product',
		'objects': lambda u: Product.objects.filter(org__managers=u),
	},
	'services': {
		'title': 'Professional service',
		'objects': lambda u: ProfessionalService.objects.filter(org__managers=u),
	},
	'organisations': {
		'title': 'Organisation',
		'objects': lambda u: Organisation.objects.filter(managers=u),
		'submit_header': 'Before submitting a new Organisation, please verify on the list of <a href="/account/orglist">current organisations</a> if the organisation already exists. If it does, please contact the manager of the organisation to gain permissions.',
	},
}

@login_required
@transaction.atomic
def profile(request):
	# We always have the user, but not always the profile. And we need a bit
	# of a hack around the normal forms code since we have two different
	# models on a single form.
	(profile, created) = UserProfile.objects.get_or_create(pk=request.user.pk)

	# Don't allow users whose accounts were created via oauth to change
	# their email, since that would kill the connection between the
	# accounts.
	can_change_email = (request.user.password != OAUTH_PASSWORD_STORE)

	# We may have a contributor record - and we only show that part of the
	# form if we have it for this user.
	try:
		contrib = Contributor.objects.get(user=request.user.pk)
	except Contributor.DoesNotExist:
		contrib = None

	contribform = None

	if request.method == 'POST':
		# Process this form
		userform = UserForm(data=request.POST, instance=request.user)
		profileform = UserProfileForm(data=request.POST, instance=profile)
		if contrib:
			contribform = ContributorForm(data=request.POST, instance=contrib)

		if userform.is_valid() and profileform.is_valid() and (not contrib or contribform.is_valid()):
			userform.save()
			profileform.save()
			if contrib:
				contribform.save()
			return HttpResponseRedirect("/account/")
	else:
		# Generate form
		userform = UserForm(instance=request.user)
		profileform = UserProfileForm(instance=profile)
		if contrib:
			contribform = ContributorForm(instance=contrib)

	return render_to_response('account/userprofileform.html', {
			'userform': userform,
			'profileform': profileform,
			'contribform': contribform,
			'can_change_email': can_change_email,
			}, NavContext(request, "account"))

@login_required
@transaction.atomic
def change_email(request):
	tokens = EmailChangeToken.objects.filter(user=request.user)
	token = len(tokens) and tokens[0] or None

	if request.user.password == OAUTH_PASSWORD_STORE:
		# Link shouldn't exist in this case, so just throw an unfriendly
		# error message.
		return HttpServerError("This account cannot change email address as it's connected to a third party login site.")

	if request.method == 'POST':
		form = ChangeEmailForm(request.user, data=request.POST)
		if form.is_valid():
			# If there is an existing token, delete it
			if token:
				token.delete()

			# Create a new token
			token = EmailChangeToken(user=request.user,
									 email=form.cleaned_data['email'].lower(),
									 token=generate_random_token())
			token.save()

			send_template_mail(settings.NOREPLY_FROM,
							   form.cleaned_data['email'],
							   'Your postgresql.org community account',
							   'account/email_change_email.txt',
							   { 'token': token , 'user': request.user, }
						   )
			return HttpResponseRedirect('done/')
	else:
		form = ChangeEmailForm(request.user)

	return render_to_response('account/emailchangeform.html', {
		'form': form,
		'token': token,
		}, NavContext(request, "account"))

@login_required
@transaction.atomic
def confirm_change_email(request, tokenhash):
	tokens = EmailChangeToken.objects.filter(user=request.user, token=tokenhash)
	token = len(tokens) and tokens[0] or None

	if request.user.password == OAUTH_PASSWORD_STORE:
		# Link shouldn't exist in this case, so just throw an unfriendly
		# error message.
		return HttpServerError("This account cannot change email address as it's connected to a third party login site.")

	if token:
		# Valid token find, so change the email address
		request.user.email = token.email.lower()
		request.user.save()
		token.delete()

	return render_to_response('account/emailchangecompleted.html', {
		'token': tokenhash,
		'success': token and True or False,
		}, NavContext(request, "account"))

@login_required
def listobjects(request, objtype):
	if not objtypes.has_key(objtype):
		raise Http404("Object type not found")
	o = objtypes[objtype]

	return render_to_response('account/objectlist.html', {
	    'objects': o['objects'](request.user),
		'title': o['title'],
		'submit_header': o.has_key('submit_header') and o['submit_header'] or None,
		'suburl': objtype,
	}, NavContext(request, 'account'))

@login_required
def orglist(request):
	orgs = Organisation.objects.filter(approved=True)

	return render_to_response('account/orglist.html', {
			'orgs': orgs,
	}, NavContext(request, 'account'))

def login(request):
	return authviews.login(request, template_name='account/login.html',
						   authentication_form=PgwebAuthenticationForm,
						   extra_context={
							   'oauth_providers': [(k,v) for k,v in sorted(settings.OAUTH.items())],
						   })

def logout(request):
	return authviews.logout_then_login(request, login_url='/')

def changepwd(request):
	if hasattr(request.user, 'password') and request.user.password == OAUTH_PASSWORD_STORE:
		return HttpServerError("This account cannot change password as it's connected to a third party login site.")

	log.info("Initiating password change from {0}".format(get_client_ip(request)))
	return authviews.password_change(request,
									 template_name='account/password_change.html',
									 post_change_redirect='/account/changepwd/done/')

def resetpwd(request):
	if request.method == "POST":
		try:
			u = User.objects.get(email__iexact=request.POST['email'])
			if u.password == OAUTH_PASSWORD_STORE:
				return HttpServerError("This account cannot change password as it's connected to a third party login site.")
		except User.DoesNotExist:
			log.info("Attempting to reset password of {0}, user not found".format(request.POST['email']))
	log.info("Initiating password set from {0}".format(get_client_ip(request)))
	return authviews.password_reset(request, template_name='account/password_reset.html',
									email_template_name='account/password_reset_email.txt',
									post_reset_redirect='/account/reset/done/')

def change_done(request):
	log.info("Password change done from {0}".format(get_client_ip(request)))
	return authviews.password_change_done(request, template_name='account/password_change_done.html')

def reset_done(request):
	log.info("Password reset done from {0}".format(get_client_ip(request)))
	return authviews.password_reset_done(request, template_name='account/password_reset_done.html')

def reset_confirm(request, uidb64, token):
	log.info("Confirming password reset for uidb {0}, token {1} from {2}".format(uidb64, token, get_client_ip(request)))
	return authviews.password_reset_confirm(request,
											uidb64=uidb64,
											token=token,
											template_name='account/password_reset_confirm.html',
											post_reset_redirect='/account/reset/complete/')

def reset_complete(request):
	log.info("Password reset completed for user from {0}".format(get_client_ip(request)))
	return authviews.password_reset_complete(request, template_name='account/password_reset_complete.html')

def signup(request):
	if request.user.is_authenticated():
		return HttpServerError("You must log out before you can sign up for a new account")

	if request.method == 'POST':
		# Attempt to create user then, eh?
		form = SignupForm(get_client_ip(request), data=request.POST)
		if form.is_valid():
			# Attempt to create the user here
			# XXX: Do we need to validate something else?
			log.info("Creating user for {0} from {1}".format(form.cleaned_data['username'], get_client_ip(request)))

			user = User.objects.create_user(form.cleaned_data['username'].lower(), form.cleaned_data['email'].lower(), last_login=datetime.now())
			user.first_name = form.cleaned_data['first_name']
			user.last_name = form.cleaned_data['last_name']

			# generate a random value for password. It won't be possible to log in with it, but
			# it creates more entropy for the token generator (I think).
			user.password = generate_random_token()
			user.save()

			# Now generate a token
			token = default_token_generator.make_token(user)
			log.info("Generated token {0} for user {1} from {2}".format(token, form.cleaned_data['username'], get_client_ip(request)))

			# Generate an outgoing email
			send_template_mail(settings.NOREPLY_FROM,
							   form.cleaned_data['email'],
							   'Your new postgresql.org community account',
							   'account/new_account_email.txt',
							   { 'uid': urlsafe_base64_encode(force_bytes(user.id)), 'token': token, 'user': user}
							   )

			return HttpResponseRedirect('/account/signup/complete/')
	else:
		form = SignupForm(get_client_ip(request))

	return render_to_response('base/form.html', {
			'form': form,
			'formitemtype': 'Account',
			'form_intro': """
To sign up for a free community account, enter your preferred userid and email address.
Note that a community account is only needed if you want to submit information - all
content is available for reading without an account.
""",
			'savebutton': 'Sign up',
			'operation': 'New',
			'recaptcha': True,
	}, NavContext(request, 'account'))


def signup_complete(request):
	return render_to_response('account/signup_complete.html', {
	}, NavContext(request, 'account'))


@transaction.atomic
def signup_oauth(request):
	if not request.session.has_key('oauth_email') \
	   or not request.session.has_key('oauth_firstname') \
	   or not request.session.has_key('oauth_lastname'):
		return HttpServerError('Invalid redirect received')

	if request.method == 'POST':
		# Second stage, so create the account. But verify that the
		# nonce matches.
		data = request.POST.copy()
		data['email'] = request.session['oauth_email'].lower()
		data['first_name'] = request.session['oauth_firstname']
		data['last_name'] = request.session['oauth_lastname']
		form = SignupOauthForm(data=data)
		if form.is_valid():
			log.info("Creating user for {0} from {1} from oauth signin of email {2}".format(form.cleaned_data['username'], get_client_ip(request), request.session['oauth_email']))

			user = User.objects.create_user(form.cleaned_data['username'].lower(),
											request.session['oauth_email'].lower(),
											last_login=datetime.now())
			user.first_name = request.session['oauth_firstname']
			user.last_name = request.session['oauth_lastname']
			user.password = OAUTH_PASSWORD_STORE
			user.save()

			# Clean up our session
			del request.session['oauth_email']
			del request.session['oauth_firstname']
			del request.session['oauth_lastname']
			request.session.modified = True

			# We can immediately log the user in because their email
			# is confirmed.
			user.backend = settings.AUTHENTICATION_BACKENDS[0]
			django_login(request, user)

			# Redirect to the sessions page, or to the account page
			# if none was given.
			return HttpResponseRedirect(request.session.pop('login_next', '/account/'))
	elif request.GET.has_key('do_abort'):
		del request.session['oauth_email']
		del request.session['oauth_firstname']
		del request.session['oauth_lastname']
		request.session.modified = True
		return HttpResponseRedirect(request.session.pop('login_next', '/'))
	else:
		# Generate possible new username
		suggested_username = request.session['oauth_email'].replace('@', '.')[:30]

		# Auto generation requires firstnamea and lastname to be specified
		f = request.session['oauth_firstname'].lower()
		l = request.session['oauth_lastname'].lower()
		if f and l:
			for u in itertools.chain([
					u"{0}{1}".format(f, l[0]),
					u"{0}{1}".format(f[0], l),
			], (u"{0}{1}{2}".format(f, l[0], n) for n in xrange(100))):
				if not User.objects.filter(username=u[:30]).exists():
					suggested_username = u[:30]
					break

		form = SignupOauthForm(initial={
			'username': suggested_username,
			'email': request.session['oauth_email'].lower(),
			'first_name': request.session['oauth_firstname'][:30],
			'last_name': request.session['oauth_lastname'][:30],
		})

	return render_to_response('account/signup_oauth.html', {
		'form': form,
		'operation': 'New account',
		'savebutton': 'Sign up for new account',
		'recaptcha': True,
		}, NavContext(request, 'account'))

####
## Community authentication endpoint
####

def communityauth(request, siteid):
	# Get whatever site the user is trying to log in to.
	site = get_object_or_404(CommunityAuthSite, pk=siteid)

	# "suburl" - old style way of passing parameters
	# deprecated - will be removed once all sites have migrated
	if request.GET.has_key('su'):
		su = request.GET['su']
		if not su.startswith('/'):
			su = None
	else:
		su = None

	# "data" - new style way of passing parameter, where we only
	# care that it's characters are what's in base64.
	if request.GET.has_key('d'):
		d = request.GET['d']
		if d != urllib.quote_plus(d, '=$'):
			# Invalid character, so drop it
			d = None
	else:
		d = None

	# Verify if the user is authenticated, and if he/she is not, generate
	# a login form that has information about which site is being logged
	# in to, and basic information about how the community login system
	# works.
	if not request.user.is_authenticated():
		if d:
			urldata = "?d=%s" % d
		elif su:
			urldata = "?su=%s" % su
		else:
			urldata = ""
		if request.method == "POST" and 'next' in request.POST and 'this_is_the_login_form' in request.POST:
			# This is a postback of the login form. So pick the next filed
			# from that one, so we keep it across invalid password entries.
			nexturl = request.POST['next']
		else:
			nexturl = '/account/auth/%s/%s' % (siteid, urldata)
		return authviews.login(request, template_name='account/login.html',
							   authentication_form=PgwebAuthenticationForm,
							   extra_context={
								   'sitename': site.name,
								   'next': nexturl,
								   'oauth_providers': [(k,v) for k,v in sorted(settings.OAUTH.items())],
							   },
						   )

	# When we reach this point, the user *has* already been authenticated.
	# The request variable "su" *may* contain a suburl and should in that
	# case be passed along to the site we're authenticating for. And of
	# course, we fill a structure with information about the user.

	if request.user.first_name=='' or request.user.last_name=='' or request.user.email=='':
		return render_to_response('account/communityauth_noinfo.html', {
				}, NavContext(request, 'account'))

	# Check for cooloff period
	if site.cooloff_hours > 0:
		if (datetime.now() - request.user.date_joined) < timedelta(hours=site.cooloff_hours):
			log.warning("User {0} tried to log in to {1} before cooloff period ended.".format(
				request.user.username, site.name))
			return render_to_response('account/communityauth_cooloff.html', {
				'site': site,
				}, NavContext(request, 'account'))

	info = {
		'u': request.user.username.encode('utf-8'),
		'f': request.user.first_name.encode('utf-8'),
		'l': request.user.last_name.encode('utf-8'),
		'e': request.user.email.encode('utf-8'),
		}
	if d:
		info['d'] = d.encode('utf-8')
	elif su:
		info['su'] = su.encode('utf-8')

	# Turn this into an URL. Make sure the timestamp is always first, that makes
	# the first block more random..
	s = "t=%s&%s" % (int(time.time()), urllib.urlencode(info))

	# Encrypt it with the shared key (and IV!)
	r = Random.new()
	iv = r.read(16) # Always 16 bytes for AES
	encryptor = AES.new(base64.b64decode(site.cryptkey), AES.MODE_CBC, iv)
	cipher = encryptor.encrypt(s + ' ' * (16-(len(s) % 16))) #Pad to even 16 bytes

	# Generate redirect
	return HttpResponseRedirect("%s?i=%s&d=%s" % (
			site.redirecturl,
			base64.b64encode(iv, "-_"),
			base64.b64encode(cipher, "-_"),
			))


def communityauth_logout(request, siteid):
	# Get whatever site the user is trying to log in to.
	site = get_object_or_404(CommunityAuthSite, pk=siteid)

	if request.user.is_authenticated():
		django_logout(request)

	# Redirect user back to the specified suburl
	return HttpResponseRedirect("%s?s=logout" % site.redirecturl)

def communityauth_search(request, siteid):
	# Perform a search for users. The response will be encrypted with the site
	# key to prevent abuse, therefor we need the site.
	site = get_object_or_404(CommunityAuthSite, pk=siteid)

	q = Q(is_active=True)
	if request.GET.has_key('s') and request.GET['s']:
		# General search term, match both name and email
		q = q & (Q(email__icontains=request.GET['s']) | Q(first_name__icontains=request.GET['s']) | Q(last_name__icontains=request.GET['s']))
	elif request.GET.has_key('e') and request.GET['e']:
		q = q & Q(email__icontains=request.GET['e'])
	elif request.GET.has_key('n') and request.GET['n']:
		q = q & (Q(first_name__icontains=request.GET['n']) | Q(last_name__icontains=request.GET['n']))
	elif request.GET.has_key('u') and request.GET['u']:
		q = q & Q(username=request.GET['u'])
	else:
		raise Http404('No search term specified')

	users = User.objects.filter(q)

	j = json.dumps([{'u': u.username, 'e': u.email, 'f': u.first_name, 'l': u.last_name} for u in users])

	# Encrypt it with the shared key (and IV!)
	r = Random.new()
	iv = r.read(16) # Always 16 bytes for AES
	encryptor = AES.new(base64.b64decode(site.cryptkey), AES.MODE_CBC, iv)
	cipher = encryptor.encrypt(j + ' ' * (16-(len(j) % 16))) #Pad to even 16 bytes

	# Base64-encode the response, just to be consistent
	return HttpResponse("%s&%s" % (
		base64.b64encode(iv, '-_'),
		base64.b64encode(cipher, '-_'),
	))
