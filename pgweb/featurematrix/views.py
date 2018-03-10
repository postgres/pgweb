from django.shortcuts import get_object_or_404

from pgweb.util.contexts import render_pgweb

from pgweb.core.models import Version
from models import Feature

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

	eol_versions = [v.tree for v in Version.objects.filter(supported=False, testing=False)]
	return render_pgweb(request, 'about', 'featurematrix/featurematrix.html', {
		'groups': groups,
		'eol_versions': eol_versions,
	})

def detail(request, featureid):
	feature = get_object_or_404(Feature, pk=featureid)
	return render_pgweb(request, 'about', 'featurematrix/featuredetail.html', {
		'feature': feature,
	})
