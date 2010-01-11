from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404

from pgweb.util.contexts import NavContext

from models import *

def root(request):
	features = Feature.objects.all().select_related().order_by('group__groupsort', 'group__groupname', 'featurename')
	groups = []
	lastgroup = -1
	currentgroup = None
	for f in features:
		if f.group.id != lastgroup:
			if currentgroup:
				groups.append(currentgroup)
			lastgroup = f.group.id
			currentgroup = {
				'group': f.group,
				'features': [],
			}
		currentgroup['features'].append(f)
	if currentgroup:
		groups.append(currentgroup)

	return render_to_response('featurematrix/featurematrix.html', {
		'groups': groups,
	}, NavContext(request, 'about'))

def detail(request, featureid):
	feature = get_object_or_404(Feature, pk=featureid)
	return render_to_response('featurematrix/featuredetail.html', {
		'feature': feature,
	}, NavContext(request, 'about'))

