from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.http import Http404
from pgweb.util.decorators import login_required
from django.db.models import Q
from django.conf import settings

from decimal import Decimal
import os

from pgweb.util.contexts import render_pgweb
from pgweb.util.helpers import template_to_string
from pgweb.util.misc import send_template_mail

from pgweb.core.models import Version

from models import DocPage
from forms import DocCommentForm

def docpage(request, version, typ, filename):
	loaddate = None
	# Get the current version both to map the /current/ url, and to later
	# determine if we allow comments on this page.
	currver = Version.objects.filter(current=True)[0].tree
	if version == 'current':
		ver = currver
	elif version == 'devel':
		if not typ == 'static':
			return HttpResponseRedirect("/docs/devel/static/%s.html" % filename)
		ver = Decimal(0)
		loaddate = Version.objects.get(tree=Decimal(0)).docsloaded
	else:
		ver = Decimal(version)
		if ver == Decimal(0):
			raise Http404("Version not found")

	if ver < Decimal("7.1") and ver > Decimal(0):
		extension = "htm"
	else:
		extension = "html"

	if ver < Decimal("7.1") and ver > Decimal(0):
		indexname = "postgres.htm"
	elif ver == Decimal("7.1"):
		indexname = "postgres.html"
	else:
		indexname = "index.html"

	if ver >= 10 and version.find('.') > -1:
		# Version 10 and up, but specified as 10.0 / 11.0 etc, so redirect back without the
		# decimal.
		return HttpResponseRedirect("/docs/{0}/static/{1}.html".format(int(ver), filename))

	fullname = "%s.%s" % (filename, extension)
	page = get_object_or_404(DocPage, version=ver, file=fullname)
	versions = DocPage.objects.extra(
		where=["file=%s OR file IN (SELECT file2 FROM docsalias WHERE file1=%s) OR file IN (SELECT file1 FROM docsalias WHERE file2=%s)"],
		params=[fullname, fullname, fullname],
		select={
			'supported':"COALESCE((SELECT supported FROM core_version v WHERE v.tree=version), 'f')",
			'testing':"COALESCE((SELECT testing FROM core_version v WHERE v.tree=version),0)",
	}).order_by('-supported', 'version').only('version', 'file')

	if typ=="interactive":
		# Interactive documents are disabled, so redirect to static page
		return HttpResponsePermanentRedirect("/docs/{0}/static/{1}.html".format(version, filename))

	return render(request, 'docs/docspage.html', {
		'page': page,
		'supported_versions': [v for v in versions if v.supported],
		'devel_versions': [v for v in versions if not v.supported and v.testing],
		'unsupported_versions': [v for v in versions if not v.supported and not v.testing],
		'title': page.title,
		'doc_index_filename': indexname,
		'loaddate': loaddate,
	})

def docsrootpage(request, version, typ):
	return docpage(request, version, typ, 'index')

def redirect_root(request, version):
	return HttpResponseRedirect("/docs/%s/static/" % version)

def root(request):
	versions = Version.objects.filter(Q(supported=True) | Q(testing__gt=0,tree__gt=0)).order_by('-tree')
	return render_pgweb(request, 'docs', 'docs/index.html', {
		'versions': versions,
	})

class _VersionPdfWrapper(object):
	"""
	A wrapper around a version that knows to look for PDF files, and
	return their sizes.
	"""
	def __init__(self, version):
		self.__version = version
		self.a4pdf = self._find_pdf('A4')
		self.uspdf = self._find_pdf('US')
		# Some versions have, ahem, strange index filenames
		if self.__version.tree < Decimal('6.4'):
			self.indexname = 'book01.htm'
		elif self.__version.tree < Decimal('7.0'):
			self.indexname = 'postgres.htm'
		elif self.__version.tree < Decimal('7.2'):
			self.indexname = 'postgres.html'
		else:
			self.indexname = 'index.html'
	def __getattr__(self, name):
		return getattr(self.__version, name)
	def _find_pdf(self, pagetype):
		try:
			return os.stat('%s/documentation/pdf/%s/postgresql-%s-%s.pdf' % (settings.STATIC_CHECKOUT, self.__version.numtree, self.__version.numtree, pagetype)).st_size
		except:
			return 0

def manuals(request):
	versions = Version.objects.filter(Q(supported=True) | Q(testing__gt=0,tree__gt=0)).order_by('-tree')
	return render_pgweb(request, 'docs', 'docs/manuals.html', {
		'versions': [_VersionPdfWrapper(v) for v in versions],
	})

def manualarchive(request):
	versions = Version.objects.filter(testing=0,supported=False,tree__gt=0).order_by('-tree')
	return render_pgweb(request, 'docs', 'docs/archive.html', {
		'versions': [_VersionPdfWrapper(v) for v in versions],
	})

@login_required
def commentform(request, itemid, version, filename):
	v = get_object_or_404(Version, tree=version)
	if not v.supported:
		# No docs comments on unsupported versions
		return HttpResponseRedirect("/docs/{0}/static/{1}".format(version, filename))

	if request.method == 'POST':
		form = DocCommentForm(request.POST)
		if form.is_valid():
			if version == '0.0':
				version = 'devel'

			send_template_mail(
				settings.DOCSREPORT_NOREPLY_EMAIL,
				settings.DOCSREPORT_EMAIL,
				'%s' % form.cleaned_data['shortdesc'],
				'docs/docsbugmail.txt', {
					'version': version,
					'filename': filename,
					'details': form.cleaned_data['details'],
				},
				usergenerated=True,
				cc=form.cleaned_data['email'],
				replyto='%s, %s' % (form.cleaned_data['email'], settings.DOCSREPORT_EMAIL),
				sendername='PG Doc comments form'
			)
			return render_pgweb(request, 'docs', 'docs/docsbug_completed.html', {})
	else:
		form = DocCommentForm(initial={
			'name': '%s %s' % (request.user.first_name, request.user.last_name),
			'email': request.user.email,
		})

	return render_pgweb(request, 'docs', 'base/form.html', {
		'form': form,
		'formitemtype': 'documentation comment',
		'operation': 'Submit',
		'form_intro': template_to_string('docs/docsbug.html', {
			'user': request.user,
		}),
		'savebutton': 'Send Email',
	})
