from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required

from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form
from pgweb.util.decorators import cache

from models import Sponsor, Server

@cache(minutes=30)
def sponsors(request):
	sponsors = Sponsor.objects.select_related().filter(sponsortype__sortkey__gt=0).order_by('sponsortype__sortkey' ,'?')
	return render_to_response('sponsors/sponsors.html', {
		'sponsors': sponsors,
	}, NavContext(request, 'about'))

def servers(request):
	servers = Server.objects.select_related().all()
	return render_to_response('sponsors/servers.html', {
		'servers': servers,
	}, NavContext(request, 'about'))

