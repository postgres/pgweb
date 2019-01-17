from datetime import date
from models import Event


def get_struct():
    now = date.today()

    # We intentionally don't put /about/eventarchive/ in the sitemap,
    # since we don't care about getting it indexed.
    # We only show events in the future, so only index events in the
    # future...

    for n in Event.objects.filter(approved=True, enddate__gt=now):
        yearsold = (now - n.startdate).days / 365
        if yearsold > 4:
            yearsold = 4
        yield ('about/event/%s/' % n.id,
               0.5 - (yearsold / 10.0))
