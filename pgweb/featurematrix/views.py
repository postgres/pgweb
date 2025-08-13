from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.template.defaultfilters import slugify

from pgweb.util.contexts import render_pgweb
from pgweb.util.decorators import content_sources
from pgweb.util.decorators import xkey

from pgweb.core.models import Version
from .models import Feature

from collections import OrderedDict
import os
import yaml

import logging
log = logging.getLogger(__name__)


# Load the feature matrix data at startup and cache it in memory
class FeatureMatrixData:
    def __init__(self):
        self.fn = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', 'data/featurematrix.yaml'))
        self.load()

    def load(self):
        self.lastload = os.stat(self.fn).st_mtime
        with open(self.fn) as f:
            self.data = yaml.load(f, Loader=yaml.SafeLoader)
        self.slugmap = {}
        for features in self.data['featurematrix'].values():
            for feature in features:
                if 'description' in feature:
                    self.slugmap[slugify(feature['name'])] = feature

    def _conditional_load(self):
        if os.stat(self.fn).st_mtime != self.lastload:
            log.info("Feature matrix data has changed, reloading")
            self.load()

    def get(self):
        self._conditional_load()
        return self.data['featurematrix']

    def feature_from_slug(self, slug):
        self._conditional_load()
        return self.slugmap.get(slug, None)

    def get_versions(self):
        self._conditional_load()
        return self.data['versions']['min'], self.data['versions']['max']

    def slug_from_legacy(self, id):
        if id in self.data['legacymap']:
            return slugify(self.data['legacymap'][id])
        return None


matrixdata = FeatureMatrixData()


def _compute_version_columns(versionspec, versions):
    currval = 'No'
    verspec = OrderedDict(versionspec)
    (lookfor, lookforval) = verspec.popitem(last=False)
    for ver in versions:
        if versionspec and ver.treestring == lookfor:
            currval = lookforval
            (lookfor, lookforval) = verspec.popitem(last=False) if verspec else (None, None)
        yield currval.lower()[:3]


@xkey('data_featurematrix')
@content_sources('style', "'unsafe-inline'")
def root(request):
    minver, maxver = matrixdata.get_versions()

    versions = list(Version.objects.filter(tree__gte=minver, tree__lte=maxver).order_by('-tree'))
    versions_rev = list(reversed(versions))

    matrix = matrixdata.get()
    # Compute the column values on each load of the page, since the list of versions may have changed.
    # (the page is cached so it's not as bad as it sounds)
    for features in matrix.values():
        for feature in features:
            feature['columns'] = reversed(list(_compute_version_columns(feature['versions'], versions_rev)))

    return render_pgweb(request, 'about', 'featurematrix/featurematrix.html', {
        'matrix': matrix,
        'versions': versions,
    })


@xkey('data_featurematrix')
def detail(request, featureslug):
    feature = matrixdata.feature_from_slug(featureslug)
    if not feature:
        raise Http404()
    return render_pgweb(request, 'about', 'featurematrix/featuredetail.html', {
        'feature': feature,
    })


@xkey('data_featurematrix')
def detail_legacy(request, featureid):
    # For now, provide a redirect on the old numeric URLs. We can eventually remove this, but let's
    # leave it for a while.
    slug = matrixdata.slug_from_legacy(int(featureid))
    if slug:
        return HttpResponseRedirect("../{}/".format(slug))
    raise Http404()
