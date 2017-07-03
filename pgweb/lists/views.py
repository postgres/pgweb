from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import json

from pgweb.util.contexts import NavContext
from pgweb.mailqueue.util import send_simple_mail

from models import MailingList, MailingListGroup
from forms import SubscribeForm

@csrf_exempt
def subscribe(request):
	if request.POST:
		form = SubscribeForm(request.POST)
		if form.is_valid():
			if form.cleaned_data['action'] == 'subscribe':
				mailsubject = "subscribe"
				# We currently only support get mail, no digest.
				# So send a regular subscribe request.
				mailtxt = "subscribe %s\n" % form.cleaned_data['lists']
			else:
				mailtxt = "unsubscribe %s\n" % form.cleaned_data['lists']
				mailsubject = "unsubscribe"

			send_simple_mail(form.cleaned_data['email'],
							 settings.LISTSERVER_EMAIL,
							 mailsubject,
							 mailtxt)

			return render_to_response('lists/subscribed.html', {
			}, NavContext(request, "community"))
	else:
		# GET, so render up the form
		form = SubscribeForm()

	return render_to_response('lists/subscribe_form.html', {
		'form': form,
		'operation': 'Legacy subscription',
		'jquery': True,
		'form_intro': """
<b>Note 1:</b> Please ensure you read the <a 
href="https://wiki.postgresql.org/wiki/Archives_Policy">Archive Policy</a>
before posting to the lists.</p>

<p><b>Note 2:</b> Please do not subscribe to mailing lists using e-mail 
accounts protected by mail-back anti-spam systems. These are extremely annoying 
to the list maintainers and other members, and you may be automatically unsubscribed."""
	}, NavContext(request, "community"))

def listinfo(request):
	resp = HttpResponse(content_type='application/json')
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

# Temporary API endpoint
def activate(request):
	if not request.META['REMOTE_ADDR'] in settings.LIST_ACTIVATORS:
		return HttpResponseForbidden()
	listname = request.GET['listname']
	active = (request.GET['active'] == '1')

	l = get_object_or_404(MailingList, listname=listname)
	if l.active == active:
		return HttpResponse("Not changed")
	l.active = active
	l.save()
	return HttpResponse("Changed")
