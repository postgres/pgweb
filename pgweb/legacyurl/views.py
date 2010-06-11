from django.http import HttpResponse, Http404, HttpResponseRedirect

def presskit(request, version, language):
	return HttpResponseRedirect("/about/press/presskit%s/%s/" % (
		version, language)
	)

def news(request, newsid):
	return HttpResponseRedirect("/about/news/%s/" % newsid)

def event(request, eventid):
	return HttpResponseRedirect("/about/event/%s/" % eventid)

def signup(request):
	return HttpResponseRedirect("/account/signup/")

def html_extension(request, prior_to_html):
	return HttpResponseRedirect("/%s" % prior_to_html)
