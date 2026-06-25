from django.db import transaction

from datetime import date

from pgweb.core.models import Version, TESTING_SHORTSTRING
from pgweb.news.models import NewsArticle, PinnedNewsArticle
from pgweb.security.models import SecurityPatch
from pgweb.util.moderation import ModerationState
from pgweb.util.versions import ParsedVersion

from pgweb.release.util import CurrentRelease


@transaction.atomic
def do_migrate():
    # Runs after migrations. Process the current release into being an actual release, if we can.
    release = CurrentRelease.get()

    if release.get('noprocess', False):
        print("Noprocess flag set on release, not processing")
        return

    if not isinstance(release['date'], date):
        raise Exception("Incorrect format of date {}".format(release['date']))

    if release['type'] in ('major', 'override') and not release.get('announcetext', None):
        raise Exception("Release type {} must specify an announcetext".format(release['type']))

    newsid = release.get('news', {}).get('id', None)
    if not newsid:
        print("No news specified for release, cannot approve news or connect CVEs")
        news = None
    else:
        try:
            news = NewsArticle.objects.get(pk=newsid)
        except NewsArticle.DoesNotExist:
            print("Could not find news article with id {}, cannot approve news or connect CVEs".format(release['news']['id']))
            news = None

    # Update latest available version
    for ver in release['versions']:
        try:
            v = Version.objects.only('tree', 'latestminor', 'reldate', 'testing').get(tree=ver.major)
            uf = []
            if v.latestminor != ver.minor:
                v.latestminor = ver.minor
                uf.append('latestminor')
                print("Set latestminor={} for version {}".format(v.latestminor, v.numtree))
            if v.reldate != release['date']:
                v.reldate = release['date']
                uf.append('reldate')
                print("Set reldate={} for version {}".format(v.reldate, v.numtree))

            if ver.testing and v.testing != ver.testing:
                v.testing = ver.testing
                v.current = False
                v.supported = False
                uf.extend(['testing', 'current', 'supported'])
                print("Set testing={}, current=False, supported=False for version {}".format(ver.type, v.numtree))

            # If we are transitioning beta -> release, set testing and supported flags.
            if v.testing != 0 and ver.type == 'major':
                v.testing = 0
                v.supported = True
                v.current = True
                uf.extend(['testing', 'supported', 'current'])
                print("Set testing=Release, supported=True and current=True for major version {}".format(v.numtree))

            if uf:
                v.save(update_fields=list(set(uf)))
        except Version.DoesNotExist:
            print("Could not find version tree {}, cannot update latest minor".format(ver.major))

    # If there are any CVEs attached to this release, add the news article to them if there is one
    if news:
        for cve in release.get('cve', []):
            try:
                patch = SecurityPatch.objects.get(cve=cve)
                patch.newspost = news
                patch.public = True
                patch.save(update_fields=['newspost', 'public'])
                print("Attached news article {} to CVE-{}".format(news.id, cve))
            except SecurityPatch.DoesNotExist:
                print("Could not find CVE {}, cannot connect to announcement")

    # If the news article isn't approved yet, bypass approval and do it!
    if news:
        if news.modstate != ModerationState.APPROVED:
            print("Approving news item {}".format(news.id))
            news.modstate = ModerationState.APPROVED
            news.date = release['date']
            news.save(update_fields=['modstate', 'date'])
            print("Sending announcement email for news item")
            news.on_approval(None)

        pa = PinnedNewsArticle.objects.all()[0]
        if pa.pinnedarticle != news:
            print("Pinning news item {}".format(news.id))
            pa.pinnedarticle = news
            pa.save(update_fields=['pinnedarticle'])
