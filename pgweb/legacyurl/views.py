from django.http import HttpResponse, Http404, HttpResponseRedirect

def presskit(request, version, language):
	return HttpResponseRedirect("/about/press/presskit%s/%s/" % (
		version, language)
	)

def news(request, newsid):
	return HttpResponseRedirect("/about/news/%s/" % newsid)

def event(request, eventid):
	return HttpResponseRedirect("/about/event/%s/" % eventid)

