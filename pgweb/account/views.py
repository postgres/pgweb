from django.contrib.auth.models import User
import django.contrib.auth.views as authviews
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.http import int_to_base36
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
import simplejson as json

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext
from pgweb.util.misc import send_template_mail
from pgweb.util.helpers import HttpServerError

from pgweb.news.models import NewsArticle
from pgweb.events.models import Event
from pgweb.core.models import Organisation, UserProfile
from pgweb.contributors.models import Contributor
from pgweb.downloads.models import Product
from pgweb.profserv.models import ProfessionalService

from models import CommunityAuthSite
from forms import SignupForm, UserForm, UserProfileForm, ContributorForm

@ssl_required
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

@ssl_required
@login_required
@transaction.commit_on_success
def profile(request):
	# We always have the user, but not always the profile. And we need a bit
	# of a hack around the normal forms code since we have two different
	# models on a single form.
	(profile, created) = UserProfile.objects.get_or_create(pk=request.user.pk)

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
			}, NavContext(request, "account"))

@ssl_required
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

@ssl_required
@login_required
def orglist(request):
	orgs = Organisation.objects.filter(approved=True)

	return render_to_response('account/orglist.html', {
			'orgs': orgs,
	}, NavContext(request, 'account'))

@ssl_required
def login(request):
	return authviews.login(request, template_name='account/login.html')

@ssl_required
def logout(request):
	return authviews.logout_then_login(request, login_url='/')

@ssl_required
def changepwd(request):
	return authviews.password_change(request,
									 template_name='account/password_change.html',
									 post_change_redirect='/account/changepwd/done/')

@ssl_required
def resetpwd(request):
	return authviews.password_reset(request, template_name='account/password_reset.html',
									email_template_name='account/password_reset_email.txt',
									post_reset_redirect='/account/reset/done/')

@ssl_required
def change_done(request):
	return authviews.password_change_done(request, template_name='account/password_change_done.html')

@ssl_required
def reset_done(request):
	return authviews.password_reset_done(request, template_name='account/password_reset_done.html')

@ssl_required
def reset_confirm(request, uidb36, token):
	return authviews.password_reset_confirm(request,
											uidb36=uidb36,
											token=token,
											template_name='account/password_reset_confirm.html',
											post_reset_redirect='/account/reset/complete/')

@ssl_required
def reset_complete(request):
	return authviews.password_reset_complete(request, template_name='account/password_reset_complete.html')

@ssl_required
def signup(request):
	if request.user.is_authenticated():
		return HttpServerError("You must log out before you can sign up for a new account")

	if request.method == 'POST':
		# Attempt to create user then, eh?
		form = SignupForm(data=request.POST)
		if form.is_valid():
			# Attempt to create the user here
			# XXX: Do we need to validate something else?

			user = User.objects.create_user(form.cleaned_data['username'].lower(), form.cleaned_data['email'])
			user.first_name = form.cleaned_data['first_name']
			user.last_name = form.cleaned_data['last_name']
			user.save()

			# Now generate a token
			token = default_token_generator.make_token(user)

			# Generate an outgoing email
			send_template_mail(settings.NOTIFICATION_FROM,
							   form.cleaned_data['email'],
							   'Your new postgresql.org community account',
							   'account/new_account_email.txt',
							   { 'uid': int_to_base36(user.id), 'token': token, 'user': user}
							   )

			return HttpResponseRedirect('/account/signup/complete/')
	else:
		form = SignupForm()

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
	}, NavContext(request, 'account'))


@ssl_required
def signup_complete(request):
	return render_to_response('account/signup_complete.html', {
	}, NavContext(request, 'account'))



####
## Community authentication endpoint
####

@ssl_required
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
		return render_to_response('account/communityauth.html', {
				'sitename': site.name,
				'next': '/account/auth/%s/%s' % (siteid, urldata),
				}, NavContext(request, 'account'))


	# When we reach this point, the user *has* already been authenticated.
	# The request variable "su" *may* contain a suburl and should in that
	# case be passed along to the site we're authenticating for. And of
	# course, we fill a structure with information about the user.

	if request.user.first_name=='' or request.user.last_name=='' or request.user.email=='':
		return render_to_response('account/communityauth_noinfo.html', {
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


@ssl_required
def communityauth_logout(request, siteid):
	# Get whatever site the user is trying to log in to.
	site = get_object_or_404(CommunityAuthSite, pk=siteid)

	if request.user.is_authenticated():
		django_logout(request)

	# Redirect user back to the specified suburl
	return HttpResponseRedirect("%s?s=logout" % site.redirecturl)

@ssl_required
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
