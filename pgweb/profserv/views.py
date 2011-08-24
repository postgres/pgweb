from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form

from models import ProfessionalService
from forms import ProfessionalServiceForm

regions = (
   ('africa','Africa'),
   ('asia','Asia'),
   ('europe','Europe'),
   ('northamerica','North America'),
   ('oceania','Oceania'),
   ('southamerica','South America'),
)

def root(request, servtype):
	title = servtype=='support' and 'Professional Services' or 'Hosting Providers'
	what = servtype=='support' and 'support' or 'hosting'
	support = servtype=='support'
	return render_to_response('profserv/root.html', {
		'title': title,
		'support': support,
		'regions': regions,
		'what': what,
	}, NavContext(request, 'support'))


def region(request, servtype, regionname):
	regname = [n for r,n in regions if r==regionname]
	if not regname:
		raise Http404
	regname = regname[0]

	what = servtype=='support' and 'support' or 'hosting'
	whatname = servtype=='support' and 'Professional Services' or 'Hosting Providers'
	title = "%s - %s" % (whatname, regname)
	support = servtype=='support'

	# DB model is a bit funky here, so use the extra-where functionality to filter properly.
	# Field names are cleaned up earlier, so it's safe against injections.
	services = ProfessionalService.objects.select_related('organisation').filter(approved=True).extra(where=["region_%s AND provides_%s" % (regionname, what),])
	
	return render_to_response('profserv/list.html', {
		'title': title,
		'support': support,
		'what': what,
		'whatname': whatname,
		'regionname': regname,
		'services': services,
	}, NavContext(request, 'support'))


# Forms to edit
@ssl_required
@login_required
def profservform(request, itemid):
	return simple_form(ProfessionalService, itemid, request, ProfessionalServiceForm)
