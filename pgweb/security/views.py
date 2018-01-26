from django.shortcuts import render_to_response, get_object_or_404

from pgweb.util.contexts import NavContext

from pgweb.core.models import Version
from models import SecurityPatch

def GetPatchesList(filt):
	return SecurityPatch.objects.raw("SELECT p.*, array_agg(CASE WHEN v.tree >= 10 THEN v.tree::int ELSE v.tree END ORDER BY v.tree) AS affected, array_agg(CASE WHEN v.tree >= 10 THEN v.tree::int ELSE v.tree END || '.' || fixed_minor ORDER BY v.tree) AS fixed FROM security_securitypatch p INNER JOIN security_securitypatchversion sv ON p.id=sv.patch_id INNER JOIN core_version v ON v.id=sv.version_id WHERE p.public AND {0} GROUP BY p.id".format(filt))

def _list_patches(request, filt):
	patches = GetPatchesList(filt)

	return render_to_response('security/security.html', {
		'patches': patches,
		'supported': Version.objects.filter(supported=True),
		'unsupported': Version.objects.filter(supported=False, tree__gt=0),
	}, NavContext(request, 'support'))

def index(request):
	# Show all supported versions
	return _list_patches(request, "v.supported")

def version(request, numtree):
	version = get_object_or_404(Version, tree=numtree)
	# It's safe to pass in the value since we get it from the module, not from
	# the actual querystring.
	return _list_patches(request, "v.id={0}".format(version.id))

	patches = SecurityPatch.objects.filter(public=True, versions=version).distinct()

	return render_to_response('security/security.html', {
		'patches': patches,
		'supported': Version.objects.filter(supported=True),
		'unsupported': Version.objects.filter(supported=False, tree__gt=0),
		'version': version,
	}, NavContext(request, 'support'))
