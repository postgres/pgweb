from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from pgweb.util.decorators import login_required

from pgweb.util.contexts import render_pgweb
from pgweb.util.helpers import simple_form

from models import NewsArticle, NewsTag
from forms import NewsArticleForm

import json


def archive(request, tag=None, paging=None):
    if tag:
        tag = get_object_or_404(NewsTag, urlname=tag.strip('/'))
        news = NewsArticle.objects.filter(approved=True, tags=tag)
    else:
        tag = None
        news = NewsArticle.objects.filter(approved=True)
    return render_pgweb(request, 'about', 'news/newsarchive.html', {
        'news': news,
        'tag': tag,
        'newstags': NewsTag.objects.all(),
    })


def item(request, itemid, throwaway=None):
    news = get_object_or_404(NewsArticle, pk=itemid)
    if not news.approved:
        raise Http404
    return render_pgweb(request, 'about', 'news/item.html', {
        'obj': news,
        'newstags': NewsTag.objects.all(),
    })


def taglist_json(request):
    return HttpResponse(json.dumps({
        'tags': [{'name': t.urlname, 'description': t.description} for t in NewsTag.objects.distinct('urlname')],
    }), content_type='application/json')


@login_required
def form(request, itemid):
    return simple_form(NewsArticle, itemid, request, NewsArticleForm,
                       redirect='/account/edit/news/')
