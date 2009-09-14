from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required

from pgweb.util.contexts import NavContext

from models import MailingList, MailingListGroup

def root(request):
	lists = MailingList.objects.all().order_by('group__sortkey', 'listname')
	
	return render_to_response('lists/root.html', {
		'lists': lists,
	}, NavContext(request, 'community'))

