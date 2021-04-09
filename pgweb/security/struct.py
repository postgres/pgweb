from datetime import date, timedelta
from .models import SecurityPatch


def get_struct():
    """create sitemap entries for each CVE entry and the top level CVE URL"""
    yield ('support/security/', None)
    for s in SecurityPatch.objects.filter(public=True).exclude(cve='').order_by('-cvenumber'):
        yield ('support/security/CVE-{}'.format(s.cve), None)
