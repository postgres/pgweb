from django.http import HttpResponse, Http404, HttpResponseRedirect

def presskit(self, version, language):
	return HttpResponseRedirect("/about/press/presskit%s/%s/" % (
		version, language)
	)

def news(self, newsid):
	return HttpResponseRedirect("/about/news/%s/" % newsid)

def event(self, eventid):
	return HttpResponseRedirect("/about/event/%s/" % eventid)

