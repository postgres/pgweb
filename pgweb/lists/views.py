from django.shortcuts import render_to_response
from django.http import HttpResponse
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
				# Default is get mail and not digest, in which case we send a regular
				# subscribe request. In other cases, we send subscribe-set which also
				# sets those flags.
				if form.cleaned_data['receive'] and not form.cleaned_data['digest']:
					mailtxt = "subscribe %s\n" % form.cleaned_data['lists']
				else:
					tags = []
					if not form.cleaned_data['receive']:
						tags.append('nomail')
					if form.cleaned_data['digest']:
						tags.append('digest')

					mailtxt = "subscribe-set %s %s\n" % (form.cleaned_data['lists'],
														",".join(tags))
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
		'operation': 'Subscribe',
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
