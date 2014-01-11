from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import simplejson as json

from pgweb.util.contexts import NavContext
from pgweb.mailqueue.util import send_simple_mail

from models import MailingList, MailingListGroup
from forms import SubscribeForm

@csrf_exempt
def subscribe(request):
	if request.POST:
		form = SubscribeForm(request.POST)
		if form.is_valid():
			mailtxt = ""
			if form.cleaned_data['action'] == 'subscribe':
				mailtxt += "subscribe %s\n" % form.cleaned_data['lists']
				if not form.cleaned_data['receive']:
					mailtxt += "set nomail\n"
				if form.cleaned_data['digest']:
					mailtxt += "set digest\n"
			else:
				mailtxt += "unsubscribe %s\n" % form.cleaned_data['lists']

			send_simple_mail(form.cleaned_data['email'],
							 settings.LISTSERVER_EMAIL,
							 '',
							 mailtxt)

			return render_to_response('lists/subscribed.html', {
			}, NavContext(request, "community"))
	else:
		# GET, so render up the form
		form = SubscribeForm()

	return render_to_response('lists/subscribe_form.html', {
		'form': form,
		'operation': 'Subscribe',
		'jquery': True,
		'form_intro': """
Please do not subscribe to mailing lists using e-mail accounts protected by
mail-back anti-spam systems. These are extremely annoying to the list maintainers
and other members, and you may be automatically unsubscribed."""
	}, NavContext(request, "community"))

def listinfo(request):
	resp = HttpResponse(mimetype='application/json')
	groupdata = [ {
			'id': g.id,
			'name': g.groupname,
			'sort': g.sortkey,
			} for g in MailingListGroup.objects.all()]
	listdata = [ {
			'id': l.id,
			'name': l.listname,
			'groupid': l.group_id,
			'active': l.active,
			'shortdesc': l.shortdesc,
			'description': l.description,
			} for l in MailingList.objects.all()]
	json.dump({'groups': groupdata, 'lists': listdata}, resp)
	return resp
