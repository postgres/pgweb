from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404
from pgweb.util.decorators import login_required

from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form

from models import NewsArticle, NewsTag
from forms import NewsArticleForm

def archive(request, tag=None, paging=None):
	if tag:
		tag = get_object_or_404(NewsTag,urlname=tag.strip('/'))
		news = NewsArticle.objects.filter(approved=True, tags=tag)
	else:
		tag = None
		news = NewsArticle.objects.filter(approved=True)
	return render_to_response('news/newsarchive.html', {
		'news': news,
		'tag': tag,
		'newstags': NewsTag.objects.all(),
	}, NavContext(request, 'about'))

def item(request, itemid, throwaway=None):
	news = get_object_or_404(NewsArticle, pk=itemid)
	if not news.approved:
		raise Http404
	return render_to_response('news/item.html', {
		'obj': news,
		'newstags': NewsTag.objects.all(),
	}, NavContext(request, 'about'))

@login_required
def form(request, itemid):
	return simple_form(NewsArticle, itemid, request, NewsArticleForm,
					   redirect='/account/edit/news/')
