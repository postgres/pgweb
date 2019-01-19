from pgweb.util.contexts import render_pgweb
from pgweb.util.decorators import cache

from .models import Sponsor, Server


@cache(minutes=30)
def sponsors(request):
    sponsors = Sponsor.objects.select_related().filter(sponsortype__sortkey__gt=0).order_by('sponsortype__sortkey', '?')
    return render_pgweb(request, 'about', 'sponsors/sponsors.html', {
        'sponsors': sponsors,
    })


def servers(request):
    servers = Server.objects.select_related().all()
    return render_pgweb(request, 'about', 'sponsors/servers.html', {
        'servers': servers,
    })
