from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required

from decimal import Decimal

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form

from pgweb.core.models import Version

from models import DocPage, DocComment
from forms import DocCommentForm

def docpage(request, version, typ, filename):
	# Get the current version both to map the /current/ url, and to later
	# determine if we allow comments on this page.
	currver = Version.objects.filter(current=True)[0].tree
	if version == 'current':
		ver = currver
	else:
		ver = Decimal(version)

	page = get_object_or_404(DocPage, version=ver, file="%s.html" % filename)

	if typ=="interactive":
		comments = DocComment.objects.filter(version=ver, file="%s.html" % filename, approved=True).order_by('posted_at')
	else:
		comments = None

	return render_to_response('docs/docspage.html', {
		'page': page,
		'title': page.title,
		'doc_nav_version': ver,
		'doc_type': typ,
		'comments': comments,
		'can_comment': (typ=="interactive" and ver==currver),
		'doc_index_filename': 'index.html',
	})

def docsrootpage(request, version, typ):
	return docpage(request, version, typ, 'index')

def redirect_root(request, version):
	return HttpResponseRedirect("/docs/%s/static/" % version)

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
