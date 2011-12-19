from django.contrib.auth.models import User
import django.contrib.auth.views as authviews
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.http import int_to_base36
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

import base64
import urllib
from Crypto.Cipher import AES
from Crypto import Random

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext
from pgweb.util.misc import send_template_mail
from pgweb.util.helpers import HttpServerError, simple_form

from pgweb.news.models import NewsArticle
from pgweb.events.models import Event
from pgweb.core.models import Organisation, UserProfile
from pgweb.downloads.models import Product
from pgweb.profserv.models import ProfessionalService

from models import CommunityAuthSite
from forms import SignupForm, UserProfileForm

@ssl_required
@login_required
def home(request):
	myarticles = NewsArticle.objects.filter(org__managers=request.user, approved=False)
	myevents = Event.objects.filter(org__managers=request.user, approved=False)
	myorgs = Organisation.objects.filter(managers=request.user, approved=False)
	myproducts = Product.objects.filter(publisher__managers=request.user, approved=False)
	myprofservs = ProfessionalService.objects.filter(organisation__managers=request.user, approved=False)
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
		'objects': lambda u: Product.objects.filter(publisher__managers=u),
	},
	'services': {
		'title': 'Professional service',
		'objects': lambda u: ProfessionalService.objects.filter(organisation__managers=u),
	},
	'organisations': {
		'title': 'Organisation',
		'objects': lambda u: Organisation.objects.filter(managers=u),
		'submit_header': 'Before submitting a new Organisation, please verify on the list of <a href="/account/orglist">current organisations</a> if the organisation already exists. If it does, please contact the manager of the organisation to gain permissions.',
	},
}

@ssl_required
@login_required
def profile(request):
	return simple_form(UserProfile, request.user.pk, request,
					   UserProfileForm, createifempty=True)

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
	return authviews.password_change(request, template_name='account/password_change.html')

@ssl_required
def resetpwd(request):
	return authviews.password_reset(request, template_name='account/password_reset.html',
									email_template_name='account/password_reset_email.txt')

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
from django.views.decorators.csrf import csrf_protect

@ssl_required
@csrf_protect
def communityauth(request, siteid):
	# Get whatever site the user is trying to log in to.
	site = get_object_or_404(CommunityAuthSite, pk=siteid)

	if request.GET.has_key('su'):
		su = request.GET['su']
		if not su.startswith('/'):
			su = None
	else:
		su = None

	# Verify if the user is authenticated, and if he/she is not, generate
	# a login form that has information about which site is being logged
	# in to, and basic information about how the community login system
	# works.
	if not request.user.is_authenticated():
		if su:
			suburl = "?su=%s" % su
		else:
			suburl = ""
		return render_to_response('account/communityauth.html', {
				'sitename': site.name,
				'next': '/account/auth/%s/%s' % (siteid, suburl),
				}, NavContext(request, 'account'))


	# When we reach this point, the user *has* already been authenticated.
	# The request variable "su" *may* contain a suburl and should in that
	# case be passed along to the site we're authenticating for. And of
	# course, we fill a structure with information about the user.

	info = {
		'u': request.user.username,
		'f': request.user.first_name,
		'l': request.user.last_name,
		'e': request.user.email,
		}
	if su:
		info['su'] = request.GET['su']

	# URL-encode the structure
	s = urllib.urlencode(info)

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
