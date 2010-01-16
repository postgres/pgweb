from django.http import HttpResponse, Http404, HttpResponseRedirect

def presskit(self, version, language):
	return HttpResponseRedirect("/about/press/presskit%s/%s/" % (
		version, language)
	)
