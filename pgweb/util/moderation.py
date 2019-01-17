# models needed to generate unapproved list
from pgweb.news.models import NewsArticle
from pgweb.events.models import Event
from pgweb.core.models import Organisation
from pgweb.downloads.models import Product
from pgweb.profserv.models import ProfessionalService
from pgweb.quotes.models import Quote

# Pending moderation requests (including URLs for the admin interface))
def _get_unapproved_list(objecttype):
    objects = objecttype.objects.filter(approved=False)
    if not len(objects): return None
    return { 'name': objects[0]._meta.verbose_name_plural, 'entries':
             [{'url': '/admin/%s/%s/%s/' % (x._meta.app_label, x._meta.model_name, x.pk), 'title': unicode(x)} for x in objects]
             }

def get_all_pending_moderations():
    applist = [
        _get_unapproved_list(NewsArticle),
        _get_unapproved_list(Event),
        _get_unapproved_list(Organisation),
        _get_unapproved_list(Product),
        _get_unapproved_list(ProfessionalService),
        _get_unapproved_list(Quote),
        ]
    return [x for x in applist if x]
