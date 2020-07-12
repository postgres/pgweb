from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404

from pgweb.util.contexts import render_pgweb
from pgweb.util.moderation import ModerationState

from .models import NewsArticle, NewsTag

import json


def archive(request, tag=None, paging=None):
    if tag:
        tag = get_object_or_404(NewsTag, urlname=tag.strip('/'))
        news = NewsArticle.objects.filter(modstate=ModerationState.APPROVED, tags=tag)
    else:
        tag = None
        news = NewsArticle.objects.filter(modstate=ModerationState.APPROVED)
    return render_pgweb(request, 'about', 'news/newsarchive.html', {
        'news': news,
        'tag': tag,
        'newstags': NewsTag.objects.all(),
    })


def item(request, itemid, throwaway=None):
    news = get_object_or_404(NewsArticle, pk=itemid)
    if news.modstate != ModerationState.APPROVED:
        raise Http404
    return render_pgweb(request, 'about', 'news/item.html', {
        'obj': news,
        'newstags': NewsTag.objects.all(),
    })


def taglist_json(request):
    return HttpResponse(json.dumps({
        'tags': [{'name': t.urlname, 'description': t.description} for t in NewsTag.objects.distinct('urlname')],
    }), content_type='application/json')
