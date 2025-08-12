from django.shortcuts import get_object_or_404

from pgweb.util.contexts import render_pgweb
from pgweb.util.decorators import content_sources

from pgweb.core.models import Version
from .models import Feature


@content_sources('style', "'unsafe-inline'")
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

    versions = Version.objects.filter(tree__gte='8.1').order_by('-tree')
    return render_pgweb(request, 'about', 'featurematrix/featurematrix.html', {
        'groups': groups,
        'versions': versions,
    })


def detail(request, featureid):
    feature = get_object_or_404(Feature, pk=featureid)
    return render_pgweb(request, 'about', 'featurematrix/featuredetail.html', {
        'feature': feature,
    })
