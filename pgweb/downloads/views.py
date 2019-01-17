from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from pgweb.util.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import os
import cPickle as pickle
import json

from pgweb.util.decorators import nocache
from pgweb.util.contexts import render_pgweb
from pgweb.util.helpers import simple_form, PgXmlHelper, HttpServerError
from pgweb.util.misc import varnish_purge, version_sort

from pgweb.core.models import Version
from models import Category, Product, StackBuilderApp
from forms import ProductForm


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
        subpath = ""

    # Pickle up the list of things we need
    try:
        f = open(settings.FTP_PICKLE, "rb")
        allnodes = pickle.load(f)
        f.close()
    except Exception, e:
        return HttpServerError(request, "Failed to load ftp site information: %s" % e)

    # An incoming subpath may either be canonical, or have one or more elements
    # present that are actually symlinks. For each element of the path, test to
    # see if it is present in the pickle. If not, look for a symlink entry with
    # and if present, replace the original entry with the symlink target.
    canonpath = ''
    if subpath != '':
        parent = ''
        for d in subpath.split('/'):
            # Check if allnodes contains a node matching the path
            if allnodes[parent].has_key(d):
                if allnodes[parent][d]['t'] == 'd':
                    canonpath = os.path.join(canonpath, d)
                elif allnodes[parent][d]['t'] == 'l':
                    canonpath = os.path.join(canonpath, allnodes[parent][d]['d']).strip('/')
                else:
                    # There's a matching node, but it's not a link or a directory
                    raise Http404

                parent = canonpath
            else:
                # There's no matching node
                raise Http404

    # If we wound up with a canonical path that doesn't match the original request,
    # redirect the user
    canonpath = canonpath.strip('/')
    if subpath != canonpath:
        return HttpResponseRedirect('/ftp/' + canonpath)

    node = allnodes[subpath]
    del allnodes

    # Add all directories
    directories = [{'link': k, 'url': k, 'type': 'd'} for k, v in node.items() if v['t'] == 'd']
    # Add all symlinks (only directories supported)
    directories.extend([{'link': k, 'url': v['d'], 'type': 'l'} for k, v in node.items() if v['t'] == 'l'])

    # A ittle early sorting wouldn't go amiss, so .. ends up at the top
    directories.sort(key=version_sort, reverse=True)

    # Add a link to the parent directory
    if subpath:
        directories.insert(0, {'link': '[Parent Directory]', 'url': '..'})

    # Fetch files
    files = [{'name': k, 'mtime': v['d'], 'size': v['s']} for k, v in node.items() if v['t'] == 'f']

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
            breadcrumbs.append({'name': pathpiece, 'path': breadroot})

    # Check if there are any "content files" we should render directly on the webpage
    file_readme = (node.has_key('README') and node['README']['t'] == 'f') and node['README']['c'] or None
    file_message = (node.has_key('.message') and node['.message']['t'] == 'f') and node['.message']['c'] or None
    file_maintainer = (node.has_key('CURRENT_MAINTAINER') and node['CURRENT_MAINTAINER']['t'] == 'f') and node['CURRENT_MAINTAINER']['c'] or None

    del node

    return render_pgweb(request, 'download', 'downloads/ftpbrowser.html', {
        'basepath': subpath.rstrip('/'),
        'directories': directories,
        'files': sorted(files),
        'breadcrumbs': breadcrumbs,
        'readme': file_readme,
        'messagefile': file_message,
        'maintainer': file_maintainer,
    })


# Accept an upload of the ftpsite pickle. This is fairly resource consuming,
# and not very optimized, but that's why we limit it so that only the ftp
# server(s) can post it.
# There is no concurrency check - the ftp site better not send more than one
# file in parallel.
@csrf_exempt
def uploadftp(request):
    if request.method != 'PUT':
        return HttpServerError(request, "Invalid method")
    if not request.META['REMOTE_ADDR'] in settings.FTP_MASTERS:
        return HttpServerError(request, "Invalid client address")
    # We have the data in request.body. Attempt to load it as
    # a pickle to make sure it's properly formatted
    pickle.loads(request.body)

    # Next, check if it's the same as the current file
    f = open(settings.FTP_PICKLE, "rb")
    x = f.read()
    f.close()
    if x == request.body:
        # Don't rewrite the file or purge any data if nothing changed
        return HttpResponse("NOT CHANGED", content_type="text/plain")

    # File has changed - let's write it!
    f = open("%s.new" % settings.FTP_PICKLE, "wb")
    f.write(request.body)
    f.close()
    os.rename("%s.new" % settings.FTP_PICKLE, settings.FTP_PICKLE)

    # Purge it out of varnish so we start responding right away
    varnish_purge("/ftp")

    # Finally, indicate to the client that we're happy
    return HttpResponse("OK", content_type="text/plain")


@csrf_exempt
def uploadyum(request):
    if request.method != 'PUT':
        return HttpServerError(request, "Invalid method")
    if not request.META['REMOTE_ADDR'] in settings.FTP_MASTERS:
        return HttpServerError(request, "Invalid client address")
    # We have the data in request.body. Attempt to load it as
    # json to ensure correct format.
    json.loads(request.body)

    # Next, check if it's the same as the current file
    if os.path.isfile(settings.YUM_JSON):
        with open(settings.YUM_JSON, "r") as f:
            if f.read() == request.body:
                # Don't rewrite the file or purge any data if nothing changed
                return HttpResponse("NOT CHANGED", content_type="text/plain")

    # File has changed - let's write it!
    with open("%s.new" % settings.YUM_JSON, "w") as f:
        f.write(request.body)

    os.rename("%s.new" % settings.YUM_JSON, settings.YUM_JSON)

    # Purge it out of varnish so we start responding right away
    varnish_purge("/download/js/yum.js")

    # Finally, indicate to the client that we're happy
    return HttpResponse("OK", content_type="text/plain")


@nocache
def mirrorselect(request, path):
    # Old access to mirrors will just redirect to the main ftp site.
    # We don't really need it anymore, but the cost of keeping it is
    # very low...
    return HttpResponseRedirect("https://ftp.postgresql.org/pub/%s" % path)


# Render javascript for yum downloads
def yum_js(request):
    with open(settings.YUM_JSON) as f:
        jsonstr = f.read()
    return render(request, 'downloads/js/yum.js', {
        'json': jsonstr,
        'supported_versions': ','.join([str(v.numtree) for v in Version.objects.filter(supported=True)]),
    }, content_type='application/json')


#######
# Product catalogue
#######
def categorylist(request):
    categories = Category.objects.all()
    return render_pgweb(request, 'download', 'downloads/categorylist.html', {
        'categories': categories,
    })


def productlist(request, catid, junk=None):
    category = get_object_or_404(Category, pk=catid)
    products = Product.objects.select_related('org', 'licencetype').filter(category=category, approved=True)
    return render_pgweb(request, 'download', 'downloads/productlist.html', {
        'category': category,
        'products': products,
        'productcount': len(products),
    })


@login_required
def productform(request, itemid):
    return simple_form(Product, itemid, request, ProductForm,
                       redirect='/account/edit/products/')


#######
# Stackbuilder
#######
def applications_v2_xml(request):
    all_apps = StackBuilderApp.objects.select_related().filter(active=True)

    resp = HttpResponse(content_type='text/xml')
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
        x.add_xml_element('manifesturl', a.manifesturl)
        for dep in a.txtdependencies.split(','):
            x.add_xml_element('dependency', dep)
        x.endElement('application')
    x.endElement('applications')
    x.endDocument()
    return resp
