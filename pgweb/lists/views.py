from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required
from django.conf import settings

from email.mime.text import MIMEText
import simplejson as json

from pgweb.util.contexts import NavContext
from pgweb.util.misc import sendmail

from models import MailingList, MailingListGroup
from forms import SubscribeForm

def root(request):
	lists = MailingList.objects.all().order_by('group__sortkey', 'listname')
	
	return render_to_response('lists/root.html', {
		'lists': lists,
	}, NavContext(request, 'community'))

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
			msg = MIMEText(mailtxt, _charset='utf-8')
			msg['Subject'] = ''
			msg['To'] = settings.LISTSERVER_EMAIL
			msg['From'] = form.cleaned_data['email']
			sendmail(msg)
			return render_to_response('lists/subscribed.html', {
			}, NavContext(request, "community"))
	else:
		# GET, so render up the form
		form = SubscribeForm()

	return render_to_response('base/form.html', {
		'form': form,
		'operation': 'Subscribe',
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
