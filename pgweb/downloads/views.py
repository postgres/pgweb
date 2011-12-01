from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.conf import settings

import os
from datetime import datetime
import urlparse
import cPickle as pickle

from pgweb.util.decorators import ssl_required, nocache
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form, PgXmlHelper, HttpServerError
from pgweb.util.misc import get_client_ip

from models import *
from forms import *

#######
# FTP browser
#######
def ftpbrowser(request, subpath):
	if subpath:
		# An actual path has been selected. Fancy!
		
		if subpath.find('..') > -1:
			# Just claim it doesn't exist if the user tries to do this
			# type of bad thing
			raise Http404
		subpath = subpath.strip('/')
	else:
		subpath=""

	# Pickle up the list of things we need
	try:
		f = open(settings.FTP_PICKLE, "rb")
		allnodes = pickle.load(f)
		f.close()
	except Exception, e:
		return HttpServerError("Failed to load ftp site information: %s" % e)

	if not allnodes.has_key(subpath):
		raise Http404

	node = allnodes[subpath]
	del allnodes

	# Add all directories
	directories = [{'link': k, 'url': k} for k,v in node.items() if v['t'] == 'd']
	# Add all symlinks (only directoreis supported)
	directories.extend([{'link': k, 'url': v['d']} for k,v in node.items() if v['t'] == 'l'])
	directories.sort()

	# Add a link to the parent directory
	if subpath:
		directories.insert(0, {'link':'[Parent Directory]', 'url':'..'})

	# Fetch files
	files = [{'name': k, 'mtime': v['d'], 'size': v['s']} for k,v in node.items() if v['t'] == 'f']
	
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

	# Check if there are any "content files" we should render directly on the webpage
	file_readme = node.has_key('README') and node['README']['c'] or None;
	file_message = node.has_key('.message') and node['.message']['c'] or None;
	file_maintainer = node.has_key('CURRENT_MAINTAINER') and node['CURRENT_MAINTAINER']['c'] or None;

	del node

	return render_to_response('downloads/ftpbrowser.html', {
		'basepath': subpath.rstrip('/'),
		'directories': directories,
		'files': sorted(files),
		'breadcrumbs': breadcrumbs,
		'readme': file_readme,
		'messagefile': file_message,
		'maintainer': file_maintainer,
	}, NavContext(request, 'download'))

def _get_numeric_ip(request):
	try:
		ip = get_client_ip(request)
		p = ip.split('.')
		return int(p[0])*16777216 + int(p[1])*65536 + int(p[2])*256 + int(p[3])
	except:
		return None

@nocache
def mirrorselect(request, path):
	# We have given up on the advanced mirror network things, and will just
	# redirect this to ftp.mirrors.postgresql.org for now...
	# Since requests hit our internal servers, we're also not going to
	# bother logging them - logging will be handled by those servers
	return HttpResponseRedirect("http://ftp.postgresql.org/pub/%s" % path)

# Accesses asking for a specific mirror will keep doing that for now.
# At some time in the future we might consider hijacking them and sending
# them to our master mirrors again.
def _mirror_redirect_internal(request, scheme, host, path):
	# Log the access
#	curs = connection.cursor()
#	curs.execute("""INSERT INTO clickthrus (scheme, host, path, country)
#VALUES (%(scheme)s, %(host)s, %(path)s, (
#SELECT countrycode FROM iptocountry WHERE %(ip)s BETWEEN startip and endip LIMIT 1))""", {
#		'scheme': scheme,
#		'host': host,
#		'path': path,
#		'ip': _get_numeric_ip(request),
#})
#	transaction.commit_unless_managed()

	# Redirect!
	newurl = "%s://%s/%s" % (scheme, host, path)
	return HttpResponseRedirect(newurl)

@nocache
def mirror_redirect(request, mirrorid, protocol, path):
	try:
		mirror = Mirror.objects.get(pk=mirrorid)
	except Mirror.DoesNotExist:
		raise Http404("Specified mirror not found")

	return _mirror_redirect_internal(
		request,
		protocol=='h' and 'http' or 'ftp',
		mirror.get_root_path(protocol),
		path,
	)

@nocache
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

def mirrors_xml(request):
	# Same as in mirrorselect
	all_mirrors = Mirror.objects.filter(mirror_active=True, mirror_private=False, mirror_dns=True).extra(where=["mirror_last_rsync>(now() - '48 hours'::interval)"]).order_by('country_name', 'mirror_index')	

	resp = HttpResponse(mimetype='text/xml')
	x = PgXmlHelper(resp)
	x.startDocument()
	x.startElement('mirrors', {})
	for m in all_mirrors:
		for protocol in m.get_all_protocols():
			x.startElement('mirror', {})
			x.add_xml_element('country', m.country_name)
			x.add_xml_element('path', m.host_path)
			x.add_xml_element('protocol', protocol)
			x.add_xml_element('hostname', m.get_host_name())
			x.endElement('mirror')
	x.endElement('mirrors')
	x.endDocument()
	return resp

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
	return simple_form(Product, itemid, request, ProductForm,
					   redirect='/account/edit/products/')

#######
# Stackbuilder
#######
def applications_v2_xml(request):
	all_apps = StackBuilderApp.objects.select_related().filter(active=True)

	resp = HttpResponse(mimetype='text/xml')
	x = PgXmlHelper(resp, skipempty=True)
	x.startDocument()
	x.startElement('applications', {})
	for a in all_apps:
		x.startElement('application', {})
		x.add_xml_element('id', a.textid)
		x.add_xml_element('platform', a.platform)
		x.add_xml_element('secondaryplatform', a.secondaryplatform)
		x.add_xml_element('version', a.version)
		x.add_xml_element('name', a.name)
		x.add_xml_element('description', a.description)
		x.add_xml_element('category', a.category)
		x.add_xml_element('pgversion', a.pgversion)
		x.add_xml_element('edbversion', a.edbversion)
		x.add_xml_element('format', a.format)
		x.add_xml_element('installoptions', a.installoptions)
		x.add_xml_element('upgradeoptions', a.upgradeoptions)
		x.add_xml_element('checksum', a.checksum)
		x.add_xml_element('mirrorpath', a.mirrorpath)
		x.add_xml_element('alturl', a.alturl)
		x.add_xml_element('versionkey', a.versionkey)
		for dep in a.dependencies.all():
			x.add_xml_element('dependency', dep.textid)
		x.endElement('application')
	x.endElement('applications')
	x.endDocument()
	return resp

