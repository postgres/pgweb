from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.http import Http404
from pgweb.util.decorators import login_required, allow_frames, content_sources
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

from .models import DocPage
from .forms import DocCommentForm


@allow_frames
@content_sources('style', "'unsafe-inline'")
def docpage(request, version, filename):
    loaddate = None
    if version == 'current':
        ver = Version.objects.filter(current=True)[0].tree
    elif version == 'devel':
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
        except:
            # If it's not a proper decimal, just return 404. This can happen from many
            # broken links around the web.
            raise Http404("Invalid version format")

        # if the version is greater than 10, truncate the number
        if release_version >= Decimal('10'):
            release_version = release_version.quantize(Decimal('1'), rounding=ROUND_DOWN)
        # if these are developer docs (i.e. from the nightly build), we need to
        # determine if these are release notes for a released version or not, i.e. if we are:
        # a) viewing the docs for a version that does not exist yet (e.g. active
        #    development before an initial beta) OR
        # b) viewing the docs for a beta version
        is_released = Version.objects.filter(tree=release_version, testing=0).exists() if version == "devel" else True
        # If we are viewing a released version of the release notesand the
        # release versions do not match, then we redirect
        if is_released and release_version != ver:
            url = "/docs/"
            if release_version >= Decimal('10'):
                url += "{}/{}".format(int(release_version), fullname)
            elif release_version < Decimal('7.2'):
                url += "7.2/{}".format(fullname)
            else:
                url += "{}/{}".format(release_version, fullname)
            return HttpResponsePermanentRedirect(url)

    page = get_object_or_404(DocPage, version=ver, file=fullname)
    versions = DocPage.objects.extra(
        where=["file=%s OR file IN (SELECT file2 FROM docsalias WHERE file1=%s) OR file IN (SELECT file1 FROM docsalias WHERE file2=%s)"],
        params=[fullname, fullname, fullname],
        select={
            'supported': "COALESCE((SELECT supported FROM core_version v WHERE v.tree=version), 'f')",
            'testing': "COALESCE((SELECT testing FROM core_version v WHERE v.tree=version),0)",
        }).order_by('-supported', 'version').only('version', 'file')

    return render(request, 'docs/docspage.html', {
        'page': page,
        'supported_versions': [v for v in versions if v.supported],
        'devel_versions': [v for v in versions if not v.supported and v.testing],
        'unsupported_versions': [v for v in versions if not v.supported and not v.testing],
        'title': page.title,
        'doc_index_filename': indexname,
        'loaddate': loaddate,
    })


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
    versions = Version.objects.filter(Q(supported=True) | Q(testing__gt=0, tree__gt=0)).order_by('-tree')
    return render_pgweb(request, 'docs', 'docs/manuals.html', {
        'versions': [_VersionPdfWrapper(v) for v in versions],
    })


def manualarchive(request):
    versions = Version.objects.filter(testing=0, supported=False, tree__gt=0).order_by('-tree')
    return render_pgweb(request, 'docs', 'docs/archive.html', {
        'versions': [_VersionPdfWrapper(v) for v in versions],
    })


def release_notes(request, major_version=None, minor_version=None):
    """Contains the main archive of release notes."""
    # this query gets a list of a unique set of release notes for each version of
    # PostgreSQL. From PostgreSQL 9.4+, release notes are only present for their
    # specific version of PostgreSQL, so all legacy release notes are present in
    # 9.3 and older
    # First the query identifies all of the release note files that have been loaded
    # into the docs. We will limit our lookup to release notes from 9.3 on up,
    # given 9.3 has all the release notes for PostgreSQL 9.3 and older
    # From there, it parses the version the release notes are for
    # from the file name, and breaks it up into "major" and "minor" version from
    # our understanding of how PostgreSQL version numbering is handled, which is
    # in 3 camps: 1 and older, 6.0 - 9.6, 10 - current
    # It is then put into a unique set
    # Lastly, we determine the next/previous versions (lead/lag) so we are able
    # to easily page between the different versions in the unique release note view
    # We only include the content if we are doing an actual lookup on an exact
    # major/minor release pair, to limit how much data we load into memory
    sql = """
    SELECT
        {content}
        file, major, minor,
        lag(minor) OVER (PARTITION BY major ORDER BY minor) AS previous,
        lead(minor) OVER (PARTITION BY major ORDER BY minor) AS next
    FROM (
        SELECT DISTINCT ON (file, major, minor)
            {content}
            file,
            CASE
                WHEN v[1]::int >= 10 THEN v[1]::numeric
                WHEN v[1]::int <= 1 THEN v[1]::int
                ELSE array_to_string(v[1:2], '.')::numeric END AS major,
            COALESCE(
                CASE
                    WHEN v[1]::int >= 10 THEN v[2]
                    WHEN v[1]::int <= 1 THEN '.' || v[2]
                    ELSE v[3]
                END::numeric, 0
            ) AS minor
        FROM (
            SELECT
                {content}
                file,
                string_to_array(regexp_replace(file, 'release-(.*)\.htm.*', '\\1'), '-') AS v
            FROM docs
            WHERE file ~ '^release-\d+' AND version >= 9.3
        ) r
    ) rr
    """
    params = []
    # if the major + minor version are provided, then we want to narrow down
    # the results to all the release notes for the minor version, as we need the
    # list of the entire set in order to generate the nice side bar in the release
    # notes
    # otherwise ensure the release notes are returned in order
    if major_version is not None and minor_version is not None:
        # at this point, include the content
        sql = sql.format(content="content,")
        # restrict to the major version, order from latest to earliest minor
        sql = """{}
        WHERE rr.major = %s
        ORDER BY rr.minor DESC""".format(sql)
        params += [major_version]
    else:
        sql = sql.format(content="")
        sql += """
        ORDER BY rr.major DESC, rr.minor DESC;
        """
    # run the query, loading a list of dict that contain all of the release
    # notes that are filtered out by the query
    release_notes = exec_to_dict(sql, params)
    # determine which set of data to pass to the template:
    # if both major/minor versions are present, we will load the release notes
    # if neither are present, we load the list of all of the release notes to list out
    if major_version is not None and minor_version is not None:
        # first, see if any release notes were returned; if not, raise a 404
        if not release_notes:
            raise Http404()
        # next, see if we can find the specific release notes we are looking for
        # format what the "minor" version should look like
        try:
            minor = Decimal('0.{}'.format(minor_version) if major_version in ['0', '1'] else minor_version)
        except TypeError:
            raise Http404()
        try:
            release_note = [r for r in release_notes if r['minor'] == minor][0]
        except IndexError:
            raise Http404()
        # of course, if nothing is found, return a 404
        if not release_note:
            raise Http404()
        context = {
            'major_version': major_version,
            'minor_version': minor_version,
            'release_note': release_note,
            'release_notes': release_notes
        }
    else:
        context = {'release_notes': release_notes}
    return render_pgweb(request, 'docs', 'docs/release_notes.html', context)


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
                usergenerated=True,
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
