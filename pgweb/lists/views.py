from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import json

from models import MailingList, MailingListGroup

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
