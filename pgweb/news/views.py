from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect
from django.template.defaultfilters import slugify

from pgweb.util.contexts import render_pgweb
from pgweb.util.moderation import ModerationState

from .models import NewsArticle, NewsTag

import datetime
import json

# Number of items per page in the news archive
NEWS_ITEMS_PER_PAGE = 10


def archive(request, tag=None, paginator=None):
    if tag and tag.strip('/'):
        tag = get_object_or_404(NewsTag, urlname=tag.strip('/'))
        news = NewsArticle.objects.select_related('org').filter(modstate=ModerationState.APPROVED, tags=tag)
    else:
        tag = None
        news = NewsArticle.objects.select_related('org').filter(modstate=ModerationState.APPROVED)
    if paginator and paginator.strip('/'):
        news = news.filter(date__lte=datetime.datetime.strptime(paginator.strip('/'), '%Y%m%d'))

    allnews = list(news.prefetch_related('tags').order_by('-date')[:NEWS_ITEMS_PER_PAGE + 1])
    if len(allnews) == NEWS_ITEMS_PER_PAGE + 1:
        # 11 means we have a second page, so set a paginator link
        paginator = allnews[NEWS_ITEMS_PER_PAGE - 1].date.strftime("%Y%m%d")
    else:
        paginator = None

    return render_pgweb(request, 'about', 'news/newsarchive.html', {
        'news': allnews[:NEWS_ITEMS_PER_PAGE],
        'paginator': paginator,
        'tag': tag,
        'newstags': NewsTag.objects.all(),
    })


def item(request, itemid, slug=None):
    news = get_object_or_404(NewsArticle, pk=itemid)
    if news.modstate != ModerationState.APPROVED:
        raise Http404
    if slug != slugify(news.title):
        return HttpResponsePermanentRedirect('/about/news/{}-{}/'.format(slugify(news.title), news.id))
    return render_pgweb(request, 'about', 'news/item.html', {
        'obj': news,
        'newstags': NewsTag.objects.all(),
    })


def taglist_json(request):
    return HttpResponse(json.dumps({
        'tags': [{
            'urlname': t.urlname,
            'name': t.name,
            'description': t.description,
            'sortkey': t.sortkey,
        } for t in NewsTag.objects.order_by('urlname').distinct('urlname')],
    }), content_type='application/json')
