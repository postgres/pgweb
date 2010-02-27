from django.contrib.auth.models import User
import django.contrib.auth.views as authviews
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseServerError
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils.http import int_to_base36
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext
from pgweb.util.misc import send_template_mail

from pgweb.news.models import NewsArticle
from pgweb.events.models import Event
from pgweb.core.models import Organisation
from pgweb.downloads.models import Product

from forms import SignupForm

@ssl_required
@login_required
def home(request):
	myarticles = NewsArticle.objects.filter(org__managers=request.user, approved=False)
	myevents = Event.objects.filter(org__managers=request.user, approved=False)
	myorgs = Organisation.objects.filter(managers=request.user, approved=False)
	myproducts = Product.objects.filter(publisher__managers=request.user, approved=False)
	return render_to_response('account/index.html', {
		'newsarticles': myarticles,
		'events': myevents,
		'organisations': myorgs,
		'products': myproducts,
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
	'organisations': {
		'title': 'Organisation',
		'objects': lambda u: Organisation.objects.filter(managers=u),
	},
}

@ssl_required
@login_required
def listobjects(request, objtype):
	if not objtypes.has_key(objtype):
		raise Http404("Object type not found")
	o = objtypes[objtype]

	return render_to_response('account/objectlist.html', {
	    'objects': o['objects'](request.user),
		'title': o['title'],
		'suburl': objtype,
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
		return HttpResponseServerError("You must log out before you can sign up for a new account")

	if request.method == 'POST':
		# Attempt to create user then, eh?
		form = SignupForm(data=request.POST)
		if form.is_valid():
			# Attempt to create the user here
			# XXX: Do we need to validate something else?

			user = User.objects.create_user(form.cleaned_data['username'], form.cleaned_data['email'])
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
			'form_intro': 'This is the intro text',
	}, NavContext(request, 'account'))


@ssl_required
def signup_complete(request):
	return render_to_response('account/signup_complete.html', {
	}, NavContext(request, 'account'))
