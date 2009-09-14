from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required

from pgweb.util.contexts import NavContext

from models import Contributor, ContributorType

def completelist(request):
	contributortypes = list(ContributorType.objects.all())
	return render_to_response('contributors/list.html', {
		'contributortypes': contributortypes,
	}, NavContext(request, 'community'))

