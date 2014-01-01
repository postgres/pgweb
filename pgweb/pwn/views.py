from django.shortcuts import render_to_response, get_object_or_404

from pgweb.util.contexts import NavContext

from datetime import date

from models import *

def index(request):
	posts = PwnPost.objects.all()

	return render_to_response('pwn/list.html', {
		'posts': posts,
	}, NavContext(request, 'community'))

def post(request, year, month, day):
	d = date(int(year), int(month), int(day))
	post = get_object_or_404(PwnPost, date=d)

	return render_to_response('pwn/view.html', {
		'post': post,
	}, NavContext(request, 'community'))
