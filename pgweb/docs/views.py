from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required

from pgweb.util.contexts import NavContext

from models import DocPage

def docpage(request, version, typ, filename):
	if version == 'current':
		#FIXME: get from settings
		ver = '8.4'
	else:
		ver = version
	page = get_object_or_404(DocPage, version=ver, file="%s.html" % filename)
	
	return render_to_response('docs/docspage.html', {
		'title': page.title,
		'doc_nav_version': version,
		'doc_type': typ,
		'page_content': page.content,
		'doc_index_filename': 'index.html',
	})

def docsrootpage(request, version, typ):
	return docpage(request, version, typ, 'index')
