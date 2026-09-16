import hashlib

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseNotModified, Http404

from pgweb.util.contexts import render_pgweb
from pgweb.util.image import get_image_contenttype_from_bytes

from .models import ContributorType, Contributor, Badge, Badgeholder


def completelist(request):
    contributortypes = list(ContributorType.objects.all())
    return render_pgweb(request, 'community', 'contributors/list.html', {
        'contributortypes': contributortypes,
    })


def peoplelist(request):
    # clamp lists to protect against unplanned floods. If we ever get close to
    # the limits, we need to make a plan on how to proceed, but we can't know
    # before we gain some practical experience
    people = Contributor.objects.prefetch_related('user')[:2000]
    badges = Badge.objects.with_has_image().filter(approved=True)[:200]
    return render_pgweb(request, 'community', 'contributors/people.html', {
        'people': people,
        'badges': badges,
    })


def badge_view(request, slug):
    badge = get_object_or_404(Badge.objects.with_has_image(), slug=slug, approved=True)
    # badge holders are users, but we want to show only users with a contributor object here
    holders = Badgeholder.objects.filter(badge=badge, user__contributor__isnull=False). \
        prefetch_related('user__contributor'). \
        order_by('user__contributor__lastname', 'user__contributor__firstname')
    return render_pgweb(request, 'community', 'contributors/badge.html', {
        'badge': badge,
        'holders': holders,
    })


def profile(request, username):
    contributor = get_object_or_404(Contributor, user__username=username)
    badges = (Badgeholder.objects.filter(user=contributor.user, badge__approved=True)
              .prefetch_related(Prefetch('badge', queryset=Badge.objects.with_has_image())))
    return render_pgweb(request, 'community', 'contributors/profile.html', {
        'contributor': contributor,
        'badges': badges,
    })


def badge_image(request, slug):
    # defer(None) clears the manager's default defer: .only() on its own
    # would leave an already-deferred field deferred and fetch it lazily.
    badge = get_object_or_404(Badge.objects.defer(None).only('slug', 'imagedata'), slug=slug, approved=True)
    if not badge.imagedata:
        raise Http404
    etag = '"' + hashlib.md5(bytes(badge.imagedata)).hexdigest() + '"'
    if request.headers.get('If-None-Match') == etag:
        return HttpResponseNotModified(headers={"ETag": etag})
    return HttpResponse(
        bytes(badge.imagedata),
        content_type=get_image_contenttype_from_bytes(badge.imagedata[:8]),
        headers={"ETag": etag},
    )
