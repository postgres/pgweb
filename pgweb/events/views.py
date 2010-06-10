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
	events = Event.objects.select_related('country').filter(approved=True).filter(training=False, enddate__gt=date.today).order_by('enddate', 'startdate',)
	training = Event.objects.select_related('country').filter(approved=True).filter(training=True, enddate__gt=date.today).order_by('enddate', 'startdate',)
	return render_to_response('events/archive.html', {
		'eventblocks': (
			{ 'name': 'Events', 'events': events, },
			{ 'name': 'Training', 'events': training, },
		),
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

