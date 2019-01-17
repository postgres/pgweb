from pgweb.util.contexts import render_pgweb

from models import ContributorType


def completelist(request):
    contributortypes = list(ContributorType.objects.all())
    return render_pgweb(request, 'community', 'contributors/list.html', {
        'contributortypes': contributortypes,
    })
