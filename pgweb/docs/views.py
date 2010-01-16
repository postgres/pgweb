from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form

from models import DocPage, DocComment
from forms import DocCommentForm

def docpage(request, version, typ, filename):
	if version == 'current':
		#FIXME: get from settings
		ver = '8.4'
	else:
		ver = version
	page = get_object_or_404(DocPage, version=ver, file="%s.html" % filename)

	if typ=="interactive":
		comments = DocComment.objects.filter(version=ver, file="%s.html" % filename, approved=True).order_by('posted_at')
	else:
		comments = None
	
	return render_to_response('docs/docspage.html', {
		'page': page,
		'title': page.title,
		'doc_nav_version': version,
		'doc_type': typ,
		'comments': comments,
		#FIXME: along with above, get from settings
		'can_comment': (typ=="interactive" and ver=='8.4'),
		'doc_index_filename': 'index.html',
	})

def docsrootpage(request, version, typ):
	return docpage(request, version, typ, 'index')

@ssl_required
@login_required
def commentform(request, itemid, version, filename):
	return simple_form(DocComment, itemid, request, DocCommentForm,
		fixedfields={
			'version': version,
			'file': filename,
		},
		redirect='/docs/comment_submitted/'
	)
