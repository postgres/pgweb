from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required

from datetime import date

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form

from models import Event
from forms import EventForm

def archive(request, paging=None):
	event = Event.objects.filter(approved=True).filter(enddate__gt=date.today)
	return render_to_response('events/archive.html', {
		'events': event,
	}, NavContext(request, 'about'))

def item(request, itemid, throwaway=None):
	event = get_object_or_404(Event, pk=itemid)
	if not event.approved:
		raise Http404
	return render_to_response('events/item.html', {
		'obj': event,
	}, NavContext(request, 'about'))

@ssl_required
@login_required
def form(request, itemid):
	return simple_form(Event, itemid, request, EventForm)

