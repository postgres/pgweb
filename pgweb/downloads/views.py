from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.conf import settings

import os
from datetime import datetime
import urlparse

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form

from models import *
from forms import *

#######
# FTP browser
#######
def _getfiledata(root, paths):
	for path in paths:
		fn = "%s/%s" % (root,path)
		if not os.path.isfile(fn):
			continue
		stat = os.stat(fn)
		yield {
			'name':path,
			'mtime': datetime.fromtimestamp(stat.st_mtime),
			'size': stat.st_size,
		}

def _getdirectorydata(root, paths):
	for path in paths:
		fn = "%s/%s" % (root,path)
		if not os.path.isdir(fn):
			continue
		if os.path.islink(fn):
			# This is a link, so change the url to point directly
			# to the link target. We'll just assume the link
			# is safe. Oh, and links must be relative
			yield {
				'link': path,
				'url': os.readlink(fn),
			}
		else:
			yield {
				'link': path,
				'url': path,
			}

def _getfile(root, filename):
	fn = "%s/%s" % (root,filename)
	if os.path.isfile(fn):
		f = open(fn)
		r = f.read()
		f.close()
		return r
	return None

def ftpbrowser(request, subpath):
	if subpath:
		# An actual path has been selected. Fancy!
		
		if subpath.find('..') > -1:
			# Just claim it doesn't exist if the user tries to do this
			# type of bad thing
			raise Http404
		fspath = os.path.join(settings.FTP_ROOT, subpath)
	else:
		fspath = settings.FTP_ROOT
		subpath=""

	if not os.path.isdir(fspath):
		raise Http404

	everything = [n for n in os.listdir(fspath) if not n.startswith('.')]

	directories = list(_getdirectorydata(fspath, everything))
	if subpath:
		directories.append({'link':'[Parent Directory]', 'url':'..'})
	files = list(_getfiledata(fspath, everything))
	
	breadcrumbs = []
	if subpath:
		breadroot = ""
		for pathpiece in subpath.split('/'):
			if not pathpiece:
				# Trailing slash will give out an empty pathpiece
				continue
			if breadroot:
				breadroot = "%s/%s" % (breadroot, pathpiece)
			else:
				breadroot = pathpiece
			breadcrumbs.append({'name': pathpiece, 'path': breadroot});

	return render_to_response('downloads/ftpbrowser.html', {
		'basepath': subpath.rstrip('/'),
		'directories': sorted(directories),
		'files': sorted(files),
		'breadcrumbs': breadcrumbs,
		'readme': _getfile(fspath, 'README'),
		'messagesfile': _getfile(fspath, '.messages'),
		'maintainer': _getfile(fspath, 'CURRENT_MAINTAINER'),
	}, NavContext(request, 'download'))

def _get_numeric_ip(request):
	try:
		ip = request.META['REMOTE_ADDR']
		p = ip.split('.')
		return int(p[0])*16777216 + int(p[1])*65536 + int(p[2])*256 + int(p[3])
	except:
		return None

def mirrorselect(request, path):
	try:
		numericip = _get_numeric_ip(request)
		near_mirrors = Mirror.objects.filter(mirror_active=True, mirror_private=False, mirror_dns=True).extra(where=["mirror_last_rsync>(now() - '48 hours'::interval)","country_code IN (SELECT lower(countrycode) FROM iptocountry WHERE %s BETWEEN startip AND endip)" % numericip]).order_by('country_name', 'mirror_index')
	except:
		near_mirrors = None
	all_mirrors = Mirror.objects.filter(mirror_active=True, mirror_private=False, mirror_dns=True).extra(where=["mirror_last_rsync>(now() - '48 hours'::interval)"]).order_by('country_name', 'mirror_index')
	return render_to_response('downloads/mirrorselect.html', {
		'path': path,
		'all_mirrors': all_mirrors,
		'near_mirrors': near_mirrors,
		'masterserver': settings.MASTERSITE_ROOT,
	}, NavContext(request, 'download'))

def _mirror_redirect_internal(request, scheme, host, path):
	# Log the access
	curs = connection.cursor()
	curs.execute("""INSERT INTO clickthrus (scheme, host, path, country)
VALUES (%(scheme)s, %(host)s, %(path)s, (
SELECT countrycode FROM iptocountry WHERE %(ip)s BETWEEN startip and endip LIMIT 1))""", {
		'scheme': scheme,
		'host': host,
		'path': path,
		'ip': _get_numeric_ip(request),
})
	transaction.commit_unless_managed()

	# Redirect!
	newurl = "%s://%s/%s" % (scheme, host, path)
	return HttpResponseRedirect(newurl)

def mirror_redirect(request, mirrorid, protocol, path):
	try:
		mirror = Mirror.objects.get(pk=mirrorid)
	except Mirror.NotFound:
		raise Http404("Specified mirror not found")

	return _mirror_redirect_internal(
		request,
		protocol=='h' and 'http' or 'ftp',
		mirror.get_root_path(protocol),
		path,
	)

def mirror_redirect_old(request):
	# Version of redirect that takes parameters in the querystring. This is
	# only used by the stackbuilder.
	if not request.GET['sb'] == "1":
		raise Http404("Page not found, you should be using the new URL format!")

	urlpieces = urlparse.urlparse(request.GET['url'])
	if urlpieces.query:
		path = "%s?%s" % (urlpieces.path, urlpieces.query)
	else:
		path = urlpieces.path

	return _mirror_redirect_internal(
		request,
		urlpieces.scheme,
		urlpieces.netloc,
		path,
	)

#######
# Product catalogue
#######
def categorylist(request):
	categories = Category.objects.all()
	return render_to_response('downloads/categorylist.html', {
		'categories': categories,
	}, NavContext(request, 'download'))

def productlist(request, catid, junk=None):
	category = get_object_or_404(Category, pk=catid)
	products = Product.objects.select_related('publisher','licencetype').filter(category=category, approved=True)
	return render_to_response('downloads/productlist.html', {
		'category': category,
		'products': products,
		'productcount': len(products),
	}, NavContext(request, 'download'))

@ssl_required
@login_required
def productform(request, itemid):
	return simple_form(Product, itemid, request, ProductForm)

