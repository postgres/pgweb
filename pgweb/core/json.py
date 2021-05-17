from django.http import JsonResponse

from .models import Version


def version_to_json(version):
    return {
        'major': str(version.numtree),
        'latestMinor': str(version.latestminor),
        'relDate': version.reldate,
        'eolDate': version.eoldate,
        'current': version.current,
        'supported': version.supported,
    }


def versions_json(request):
    versions = list(map(version_to_json, Version.objects
                        .filter(tree__gt=0).filter(testing=0)
                        .order_by('tree')))
    return JsonResponse(versions, safe=False, json_dumps_params={'sort_keys': True})
