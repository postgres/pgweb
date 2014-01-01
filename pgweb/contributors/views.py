from django.shortcuts import render_to_response

from pgweb.util.contexts import NavContext

from models import ContributorType

def completelist(request):
	contributortypes = list(ContributorType.objects.all())
	return render_to_response('contributors/list.html', {
		'contributortypes': contributortypes,
	}, NavContext(request, 'community'))

