from django.shortcuts import get_object_or_404
from django.http import Http404

from datetime import date

from pgweb.util.contexts import render_pgweb

from .models import Event


def main(request):
    return render_pgweb(request, 'about', 'events/archive.html', {
        'title': 'Upcoming Events',
        'events': Event.objects.select_related('country').filter(approved=True, enddate__gt=date.today()).order_by('enddate', 'startdate'),
    })


def _eventarchive(request, title):
    # Hardcode to the latest 100 events. Do we need paging too?
    events = Event.objects.select_related('country', 'language').filter(approved=True).filter(enddate__lte=date.today()).order_by('-enddate', '-startdate',)[:100]
    return render_pgweb(request, 'about', 'events/archive.html', {
        'title': '%s Archive' % title,
        'archive': True,
        'events': events,
    })


def archive(request):
    return _eventarchive(request, 'Event')


def item(request, itemid, throwaway=None):
    event = get_object_or_404(Event, pk=itemid)
    if not event.approved:
        raise Http404
    return render_pgweb(request, 'about', 'events/item.html', {
        'obj': event,
    })
