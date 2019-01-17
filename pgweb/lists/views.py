from django.http import HttpResponse

import json

from models import MailingList, MailingListGroup


def listinfo(request):
    resp = HttpResponse(content_type='application/json')
    groupdata = [{
        'id': g.id,
        'name': g.groupname,
        'sort': g.sortkey,
    } for g in MailingListGroup.objects.all()]
    listdata = [{
        'id': l.id,
        'name': l.listname,
        'groupid': l.group_id,
        'active': l.active,
        'shortdesc': l.shortdesc,
        'description': l.description,
    } for l in MailingList.objects.all()]
    json.dump({'groups': groupdata, 'lists': listdata}, resp)
    return resp
