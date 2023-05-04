from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseNotFound
from django.http import HttpResponse, Http404
from pgweb.util.decorators import login_required, content_sources, allow_frames
from django.template.defaultfilters import strip_tags
from django.db.models import Q
from django.conf import settings

from decimal import Decimal, ROUND_DOWN
import os
import re

from pgweb.util.contexts import render_pgweb
from pgweb.util.helpers import template_to_string
from pgweb.util.misc import send_template_mail

from pgweb.core.models import Version
from pgweb.util.db import exec_to_dict

from .models import DocPage, DocPageRedirect
from .forms import DocCommentForm


def _versioned_404(msg, version):
    r = HttpResponseNotFound(msg)
    r['xkey'] = 'pgdocs_{}'.format(version)
    return r


@content_sources('style', "'unsafe-inline'")
def docpage(request, version, filename):
    loaddate = None
    loadgit = None
    if version == 'current':
        ver = Version.objects.filter(current=True)[0].tree
    elif version == 'devel':
        ver = Decimal(0)
        verobj = Version.objects.get(tree=Decimal(0))
        loaddate = verobj.docsloaded
        loadgit = verobj.docsgit
    else:
        ver = Decimal(version)
        if ver == Decimal(0):
            return _versioned_404("Version not found", "all")

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
        return HttpResponsePermanentRedirect("/docs/{0}/{1}.html".format(int(ver), filename))

    fullname = "%s.%s" % (filename, extension)

    # Before looking up the documentation, we need to make a check for release
    # notes. Based on a change, from PostgreSQL 9.4 and up, release notes are
    # only available for the current version (e.g. 11 only has 11.0, 11.1, 11.2)
    # This checks to see if there is a mismatch (e.g. ver = 9.4, fullname = release-9-3-2.html)
    # or if these are the development docs that are pointing to a released version
    # and performs a redirect to the older version
    if fullname.startswith('release-') and (ver >= Decimal("9.4") or version == "devel") and not fullname.startswith('release-prior'):
        # figure out which version to redirect to. Note that the oldest version
        # of the docs loaded is 7.2
        release_version = re.sub(r'release-((\d+)(-\d+)?)(-\d+)?.html',
                                 r'\1', fullname).replace('-', '.')
        # convert to Decimal for ease of manipulation
        try:
            release_version = Decimal(release_version)
        except Exception as e:
            # If it's not a proper decimal, just return 404. This can happen from many
            # broken links around the web.
            raise Http404("Invalid version format")

        # if the version is greater than 10, truncate the number
        if release_version >= Decimal('10'):
            release_version = release_version.quantize(Decimal('1'), rounding=ROUND_DOWN)
        # if these are developer docs (i.e. from the nightly build), we need to
        # determine if these are release notes for a branched version or not,
        # i.e. if we are:
        # a) viewing the docs for a version that does not exist yet (e.g. active
        #    development before an initial beta) OR
        # b) viewing the docs for a beta, RC, or fully released version
        is_branched = Version.objects.filter(tree=release_version).exists() if version == "devel" else True
        # If we are viewing a released version of the release notesand the
        # release versions do not match, then we redirect
        if is_branched and release_version != ver:
            url = "/docs/"
            if release_version >= Decimal('10'):
                url += "{}/{}".format(int(release_version), fullname)
            elif release_version < Decimal('7.2'):
                url += "7.2/{}".format(fullname)
            else:
                url += "{}/{}".format(release_version, fullname)
            return HttpResponsePermanentRedirect(url)

    # try to get the page outright. If it's not found, check to see if it's a
    # doc alias with a redirect, and if so, redirect to that page
    try:
        page = DocPage.objects.select_related('version').get(version=ver, file=fullname)
    except DocPage.DoesNotExist:
        # if the page does not exist but there is a special page redirect, check
        # for the existence of that. if that does not exist, then we're really
        # done and can 404
        try:
            page_redirect = DocPageRedirect.objects.get(redirect_from=fullname)
            url = "/docs/{}/{}".format(version, page_redirect.redirect_to)
            return HttpResponsePermanentRedirect(url)
        except DocPageRedirect.DoesNotExist:
            return _versioned_404("Page not found", ver)

    versions = DocPage.objects.select_related('version').extra(
        where=["file=%s OR file IN (SELECT file2 FROM docsalias WHERE file1=%s) OR file IN (SELECT file1 FROM docsalias WHERE file2=%s)"],
        params=[fullname, fullname, fullname],
    ).order_by('-version__supported', 'version').only('version', 'file')

    # If possible (e.g. if we match), remove the header part of the docs so that we can generate a plain text
    # preview. For older versions where this doesn't match, we just leave it empty.
    m = re.match(r'^<div [^>]*class="navheader"[^>]*>.*?</div>(.*)$', page.content, re.S)
    if m:
        contentpreview = strip_tags(m.group(1))
    else:
        contentpreview = ''

    # determine the canonical version of the page
    # if the doc page is in the current version, then we set it to current
    # otherwise, check the supported and unsupported versions and find the
    # last version that the page appeared
    # we exclude "devel" as development docs are disallowed in robots.txt
    canonical_version = ""
    if len(list(filter(lambda v: v.version.current, versions))):
        canonical_version = "current"
    else:
        version_max = None
        for v in versions:
            if version_max is None:
                version_max = v
            elif v.version.tree > version_max.version.tree:
                version_max = v
        if version_max.version.tree > Decimal(0):
            canonical_version = version_max.display_version()

    r = render(request, 'docs/docspage.html', {
        'page': page,
        'supported_versions': [v for v in versions if v.version.supported],
        'devel_versions': [v for v in versions if not v.version.supported and v.version.testing],
        'unsupported_versions': [v for v in versions if not v.version.supported and not v.version.testing],
        'canonical_version': canonical_version,
        'title': page.title,
        'doc_index_filename': indexname,
        'loaddate': loaddate,
        'loadgit': loadgit,
        'og': {
            'url': '/docs/{}/{}'.format(page.display_version(), page.file),
            'time': page.version.docsloaded,
            'title': page.title.strip(),
            'description': contentpreview,
            'sitename': 'PostgreSQL Documentation',
        }
    })
    r['xkey'] = 'pgdocs_{}'.format(page.display_version())
    if version == 'current':
        r['xkey'] += ' pgdocs_current'
    return r


@allow_frames
@content_sources('style', "'unsafe-inline'")
def docsvg(request, version, filename):
    if version == 'current':
        ver = Version.objects.filter(current=True)[0].tree
    elif version == 'devel':
        ver = Decimal(0)
    else:
        ver = Decimal(version)
        if ver == Decimal(0):
            return _versioned_404("Version not found", "all")

    if ver < Decimal(12) and ver > Decimal(0):
        raise Http404("SVG images don't exist in this version")

    page = get_object_or_404(DocPage, version=ver, file="{0}.svg".format(filename))

    r = HttpResponse(page.content, content_type="image/svg+xml")
    r['xkey'] = 'pgdocs_{}'.format(page.display_version())
    if version == 'current':
        r['xkey'] += ' pgdocs_current'
    return r


def docspermanentredirect(request, version, typ, page, *args):
    """Provides a permanent redirect from the old static/interactive pages to
    the modern pages that do not have said keywords.
    """
    url = "/docs/%s/" % version
    if page:
        url += page
    return HttpResponsePermanentRedirect(url)


def docsrootpage(request, version):
    return docpage(request, version, 'index')


def redirect_root(request, version):
    return HttpResponsePermanentRedirect("/docs/%s/" % version)


def root(request):
    versions = Version.objects.filter(Q(supported=True) | Q(testing__gt=0, tree__gt=0)).order_by('-tree')
    r = render_pgweb(request, 'docs', 'docs/index.html', {
        'versions': [_VersionPdfWrapper(v) for v in versions],
    })
    r['xkey'] = 'pgdocs_all pgdocs_pdf'
    return r


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
        except Exception as e:
            return 0


def manuals(request):
    # Legacy URL for manuals, redirect to the main docs page
    return HttpResponsePermanentRedirect('/docs/')


def manualarchive(request):
    versions = Version.objects.filter(testing=0, supported=False, tree__gt=0).order_by('-tree')
    r = render_pgweb(request, 'docs', 'docs/archive.html', {
        'versions': [_VersionPdfWrapper(v) for v in versions],
    })
    r['xkey'] = 'pgdocs_all pgdocs_pdf'
    return r


# Store a list of versions for which we have release notes, but nothing else,
# so we don't have to add them to core_version.
# NOTE! Order-sensitive!
_release_notes_only_versions = [
    # PostgreSQL 6.2
    [Decimal('6.2'), 1],
    [Decimal('6.2'), 0],
    # PostgreSQL 6.1
    [Decimal('6.1'), 1],
    [Decimal('6.1'), 0],
    # PostgreSQL 6.0
    [Decimal('6.0'), 0],
    # PostgresSQL 1
    [1, 9],
    [1, 2],
    [1, 1],
    [1, 0],
    # Postgres95
    [0, 3],
    [0, 2],
    [0, 1],
]
release_notes_only_versions = [{'major': major, 'minor': minor} for major, minor in _release_notes_only_versions]


def release_notes_list(request):
    """Lists the available release notes"""
    # We only keep 6.3 and newer in core_version (for legacy reasons)
    releases = exec_to_dict("SELECT tree AS major, minor FROM core_version INNER JOIN generate_series(0, latestminor) g(minor) ON true WHERE testing=0 AND tree > 6.2 ORDER BY tree DESC, minor DESC")

    r = render_pgweb(request, 'docs', 'docs/release_notes_list.html', {
        'releases': releases + release_notes_only_versions,
    })
    r['xkey'] = 'pgdocs_all'
    return r


def release_notes(request, version):
    """Contains the main archive of release notes."""

    version_pieces = version.split('.')  # Gives 1, 2 or 3 pieces due to regexp
    if len(version_pieces) == 3:
        # This is always major.major.minor
        major_version = Decimal('.'.join(version_pieces[0:2]))
        minor_version = Decimal(version_pieces[2])
        if major_version >= 10:
            # There is no three-digit version for 10+, so redirect back
            return HttpResponseRedirect('/docs/release/{}/'.format(major_version))
        if minor_version > 0:
            version_file = 'release-{}-{}.html'.format(str(major_version).replace('.', '-'), minor_version)
        else:
            version_file = 'release-{}.html'.format(str(major_version).replace('.', '-'))
    elif len(version_pieces) == 2:
        # This can be either a full version (10.3) *or* it can be
        # a major version without minor (9.5).
        major_version = Decimal(version_pieces[0])
        minor_version = Decimal(version_pieces[1])
        if int(version_pieces[0]) >= 10 or int(version_pieces[0]) <= 1:
            if major_version > 1:
                if minor_version == 0:
                    version_file = 'release-{}.html'.format(major_version)
                else:
                    version_file = 'release-{}-{}.html'.format(major_version, minor_version)
            elif major_version in (0, 1):
                if minor_version == 0:
                    version_file = 'release-{}-0.html'.format(major_version)
                else:
                    version_file = 'release-{}-{:02}.html'.format(major_version, minor_version)
        else:
            # Major version without a minor we redirect to the .0 minor
            return HttpResponseRedirect('/docs/release/{}.{}.0/'.format(major_version, minor_version))
    else:
        # Single digit major version, so redirect to a point-zero version of it
        if version_pieces[0] == '0':
            # Postgres95 did not have a .0 version :O
            return HttpResponseRedirect('/docs/release/0.1/')
        else:
            return HttpResponseRedirect('/docs/release/{}.0/'.format(Decimal(version_pieces[0])))

    # If we have an exact match for our major version, get that one. If not, get the release
    # notes from the highest available version.
    release_notes = exec_to_dict("SELECT content FROM docs WHERE file=%(filename)s AND version > 0 ORDER BY version=%(major_version)s DESC, version DESC LIMIT 1", {
        'filename': version_file,
        'major_version': major_version,
    })
    try:
        release_note = release_notes[0]
    except IndexError:
        # Must version this one, as this minor version can show up later and in that case we
        # need it to render once purged.
        return _versioned_404("Minor version release notes not found", major_version)

    # We only keep 6.3 and newer in core_version (for legacy reasons)
    if major_version > 6.2:
        available_minor_versions = exec_to_dict("SELECT minor FROM generate_series(0, (SELECT latestminor FROM core_version WHERE tree=%(major_version)s)) g(minor) ORDER BY minor DESC", {
            'major_version': major_version,
        })
        previous_minor = minor_version - 1 if minor_version > 0 else None
        next_minor = minor_version + 1 if minor_version < available_minor_versions[0]['minor'] else None
    else:
        available_minor_versions = [v for v in release_notes_only_versions if v['major'] == major_version]
        # Ugh, there are gaps, so we have to do it the ugly way
        previous_minor = None
        next_minor = None
        for i, v in enumerate(available_minor_versions):
            if v['minor'] == minor_version:
                if i > 0:
                    next_minor = available_minor_versions[i - 1]['minor']
                if v != available_minor_versions[-1]:
                    previous_minor = available_minor_versions[i + 1]['minor']
                break

    r = render_pgweb(request, 'docs', 'docs/release_notes.html', {
        'major_version': major_version,
        'minor_version': minor_version,
        'release_note': release_note,
        'available_minor_versions': available_minor_versions,
        'previous_minor_release': previous_minor,
        'next_minor_release': next_minor,
    })
    r['xkey'] = 'pgdocs_{}'.format(major_version)
    return r


@login_required
def commentform(request, itemid, version, filename):
    if version == 'current':
        v = Version.objects.get(current=True)
    else:
        v = get_object_or_404(Version, tree=version)
    if not v.supported:
        # No docs comments on unsupported versions
        return HttpResponseRedirect("/docs/{0}/{1}".format(version, filename))

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
                cc=form.cleaned_data['email'],
                replyto='%s, %s' % (form.cleaned_data['email'], settings.DOCSREPORT_EMAIL),
                sendername='PG Doc comments form'
            )
            return HttpResponseRedirect("done/")
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


@login_required
def commentform_done(request, itemid, version, filename):
    return render_pgweb(request, 'docs', 'docs/docsbug_completed.html', {})
