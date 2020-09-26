from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.http import HttpResponseNotModified
from django.core.exceptions import PermissionDenied
from django.template import TemplateDoesNotExist, loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.tokens import default_token_generator
from pgweb.util.decorators import login_required, content_sources
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db import connection, transaction
from django.utils.http import http_date, parse_http_date
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
import django

from datetime import date, datetime, timedelta
import os
import re
import urllib.parse
import hashlib
import logging

from pgweb.util.decorators import cache, nocache
from pgweb.util.contexts import render_pgweb, get_nav_menu, PGWebContextProcessor
from pgweb.util.helpers import PgXmlHelper
from pgweb.util.moderation import get_all_pending_moderations, get_moderation_model, ModerationState
from pgweb.util.misc import get_client_ip, varnish_purge, varnish_purge_expr, varnish_purge_xkey
from pgweb.util.misc import send_template_mail
from pgweb.util.sitestruct import get_all_pages_struct
from pgweb.mailqueue.util import send_simple_mail
from pgweb.account.views import OAUTH_PASSWORD_STORE

# models needed for the pieces on the frontpage
from pgweb.news.models import NewsArticle, NewsTag
from pgweb.events.models import Event
from pgweb.quotes.models import Quote
from .models import Version, ImportedRSSItem, ModerationNotification

# models needed for the pieces on the community page
from pgweb.survey.models import Survey

# models and forms needed for core objects
from .models import Organisation
from .forms import MergeOrgsForm, ModerationForm, AdminResetPasswordForm

log = logging.getLogger(__name__)


# Front page view
@cache(minutes=10)
def home(request):
    news = NewsArticle.objects.filter(modstate=ModerationState.APPROVED)[:5]
    today = date.today()
    # get up to seven events to display on the homepage
    event_base_queryset = Event.objects.select_related('country').filter(
        approved=True,
        enddate__gte=today,
    )
    # first, see if there are up to two non-badged events within 90 days
    other_events = event_base_queryset.filter(
        badged=False,
        startdate__lte=today + timedelta(days=90),
    ).order_by('enddate', 'startdate')[:2]
    # based on that, get 7 - |other_events| community events to display
    community_event_queryset = event_base_queryset.filter(badged=True).order_by('enddate', 'startdate')[:(7 - other_events.count())]
    # now, return all the events in one unioned array!
    events = community_event_queryset.union(other_events).order_by('enddate', 'startdate').all()
    versions = Version.objects.filter(supported=True)
    planet = ImportedRSSItem.objects.filter(feed__internalname="planet").order_by("-posttime")[:9]

    return render(request, 'index.html', {
        'title': 'The world\'s most advanced open source database',
        'news': news,
        'newstags': NewsTag.objects.all(),
        'events': events,
        'versions': versions,
        'planet': planet,
    })


# About page view (contains information about PostgreSQL + random quotes)
@cache(minutes=10)
def about(request):
    # get 5 random quotes
    quotes = Quote.objects.filter(approved=True).order_by('?').all()[:5]
    return render_pgweb(request, 'about', 'core/about.html', {
        'quotes': quotes,
    })


# Community main page (contains surveys and potentially more)
def community(request):
    s = Survey.objects.filter(current=True)
    try:
        s = s[0]
    except Exception as e:
        s = None
    planet = ImportedRSSItem.objects.filter(feed__internalname="planet").order_by("-posttime")[:7]
    return render_pgweb(request, 'community', 'core/community.html', {
        'survey': s,
        'planet': planet,
    })


# List of supported versions
def versions(request):
    return render_pgweb(request, 'support', 'support/versioning.html', {
        'versions': Version.objects.filter(tree__gt=0).filter(testing=0),
    })


re_staticfilenames = re.compile("^[0-9A-Z/_-]+$", re.IGNORECASE)


# Generic fallback view for static pages
def fallback(request, url):
    if url.find('..') > -1:
        raise Http404('Page not found.')

    if not re_staticfilenames.match(url):
        raise Http404('Page not found.')

    if len(url) > 250:
        # Maximum length is really per-directory, but we shouldn't have any pages/fallback
        # urls with anywhere *near* that, so let's just limit it on the whole
        raise Http404('Page not found.')

    try:
        t = loader.get_template('pages/%s.html' % url)
    except TemplateDoesNotExist:
        try:
            t = loader.get_template('pages/%s/en.html' % url)
        except TemplateDoesNotExist:
            raise Http404('Page not found.')

    # Guestimate the nav section by looking at the URL and taking the first
    # piece of it.
    try:
        navsect = url.split('/', 2)[0]
    except Exception as e:
        navsect = ''
    c = PGWebContextProcessor(request)
    c.update({'navmenu': get_nav_menu(navsect)})
    return HttpResponse(t.render(c))


# robots.txt
def robots(request):
    return HttpResponse("""User-agent: *
Disallow: /admin/
Disallow: /account/
Disallow: /docs/devel/
Disallow: /list/
Disallow: /search/
Disallow: /message-id/raw/
Disallow: /message-id/flat/

Sitemap: https://www.postgresql.org/sitemap.xml
""", content_type='text/plain')


def _make_sitemap(pagelist):
    resp = HttpResponse(content_type='text/xml')
    x = PgXmlHelper(resp)
    x.startDocument()
    x.startElement('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})
    pages = 0
    for p in pagelist:
        pages += 1
        x.startElement('url', {})
        x.add_xml_element('loc', 'https://www.postgresql.org/%s' % urllib.parse.quote(p[0]))
        if len(p) > 1 and p[1]:
            x.add_xml_element('priority', str(p[1]))
        if len(p) > 2 and p[2]:
            x.add_xml_element('lastmod', p[2].isoformat() + "Z")
        x.endElement('url')
    x.endElement('urlset')
    x.endDocument()
    return resp


# Sitemap (XML format)
@cache(hours=6)
def sitemap(request):
    return _make_sitemap(get_all_pages_struct())


# Internal sitemap (only for our own search engine)
# Note! Still served up to anybody who wants it, so don't
# put anything secret in it...
@cache(hours=6)
def sitemap_internal(request):
    return _make_sitemap(get_all_pages_struct(method='get_internal_struct'))


# dynamic CSS serving, meaning we merge a number of different CSS into a
# single one, making sure it turns into a single http response. We do this
# dynamically, since the output will be cached.
_dynamic_cssmap = {
    'base': ['media/css/main.css',
             'media/css/normalize.css', ],
}


@cache(hours=6)
def dynamic_css(request, css):
    if css not in _dynamic_cssmap:
        raise Http404('CSS not found')
    files = _dynamic_cssmap[css]
    resp = HttpResponse(content_type='text/css')

    # We honor if-modified-since headers by looking at the most recently
    # touched CSS file.
    latestmod = 0
    for fn in files:
        try:
            stime = os.stat(fn).st_mtime
            if latestmod < stime:
                latestmod = stime
        except OSError:
            # If we somehow referred to a file that didn't exist, or
            # one that we couldn't access.
            raise Http404('CSS (sub) not found')
    if 'HTTP_IF_MODIFIED_SINCE' in request.META:
        # This code is mostly stolen from django :)
        matches = re.match(r"^([^;]+)(; length=([0-9]+))?$",
                           request.META.get('HTTP_IF_MODIFIED_SINCE'),
                           re.IGNORECASE)
        header_mtime = parse_http_date(matches.group(1))
        # We don't do length checking, just the date
        if int(latestmod) <= header_mtime:
            return HttpResponseNotModified(content_type='text/css')
    resp['Last-Modified'] = http_date(latestmod)

    for fn in files:
        with open(fn) as f:
            resp.write("/* %s */\n" % fn)
            resp.write(f.read())
            resp.write("\n")

    return resp


@nocache
def csrf_failure(request, reason=''):
    resp = render(request, 'errors/csrf_failure.html', {
        'reason': reason,
    })
    resp.status_code = 403  # Forbidden
    return resp


# Basic information about the connection
@cache(seconds=30)
def system_information(request):
    return render(request, 'core/system_information.html', {
        'server': os.uname()[1],
        'cache_server': request.META['REMOTE_ADDR'] or None,
        'client_ip': get_client_ip(request),
        'django_version': django.get_version(),
    })


# Sync timestamp for automirror. Keep it around for 30 seconds
# Basically just a check that we can access the backend still...
@cache(seconds=30)
def sync_timestamp(request):
    s = datetime.now().strftime("%Y-%m-%d %H:%M:%S\n")
    r = HttpResponse(s, content_type='text/plain')
    r['Content-Length'] = len(s)
    return r


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_resetpassword(request, userid):
    user = get_object_or_404(User, pk=userid)

    if request.method == 'POST':
        form = AdminResetPasswordForm(data=request.POST)
        if form.is_valid():
            log.info("Admin {0} initiating password reset for {1}".format(request.user.username, user.email))
            token = default_token_generator.make_token(user)
            send_template_mail(
                settings.ACCOUNTS_NOREPLY_FROM,
                user.email,
                'Password reset for your postgresql.org account',
                'account/password_reset_email.txt',
                {
                    'user': user,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token,
                },
            )
            messages.info(request, "Password reset token sent.")
            return HttpResponseRedirect("../")
    else:
        form = AdminResetPasswordForm()

    return render(request, 'core/admin_reset_password.html', {
        'is_oauth': user.password == OAUTH_PASSWORD_STORE,
        'user': user,
        'form': form,
    })


# List of all unapproved objects, for the special admin page
@login_required
@user_passes_test(lambda u: u.is_staff)
@user_passes_test(lambda u: u.groups.filter(name='pgweb moderators').exists())
def admin_pending(request):
    return render(request, 'core/admin_pending.html', {
        'app_list': get_all_pending_moderations(),
    })


def _send_moderation_message(request, obj, message, notice, what):
    if message and notice:
        msg = "{}\n\nThe following further information was provided:\n{}".format(message, notice)
    elif notice:
        msg = notice
    else:
        msg = message

    n = ModerationNotification(
        objectid=obj.id,
        objecttype=type(obj).__name__,
        text=msg,
        author=request.user,
    )
    n.save()

    # In the email, add a link back to the item in the bottom
    msg += "\n\nYou can view your {} by going to\n{}/account/edit/{}/".format(
        obj._meta.verbose_name,
        settings.SITE_ROOT,
        obj.account_edit_suburl,
    )

    # Send message to org admins
    if isinstance(obj, Organisation):
        org = obj
    else:
        org = obj.org

    for m in org.managers.all():
        send_simple_mail(
            settings.NOTIFICATION_FROM,
            m.email,
            "Your submitted {} with title {}".format(obj._meta.verbose_name, obj.title),
            msg,
            suppress_auto_replies=False,
            receivername='{} {}'.format(m.first_name, m.last_name),
        )

    # Send notification to admins
    if what:
        admmsg = message
        if obj.is_approved:
            admmsg += "\n\nNOTE! This {} was previously approved!!".format(obj._meta.verbose_name)

        if notice:
            admmsg += "\n\nModeration notice:\n{}".format(notice)

        if what != "rejected":
            # No point in sending an edit link to a page that doesn't exist anymore
            admmsg += "\n\nEdit at: {}/admin/_moderate/{}/{}/\n".format(settings.SITE_ROOT, obj._meta.model_name, obj.id)

        if obj.twomoderators and obj.firstmoderator:
            # For two-moderator objects, only one is required to reject or send back for editing. In that case,
            # just log the current user who is the one that did that.
            modname = "{} and {}".format(obj.firstmoderator, request.user)
        else:
            modname = request.user

        send_simple_mail(settings.NOTIFICATION_FROM,
                         settings.NOTIFICATION_EMAIL,
                         "{} '{}' {} by {}".format(obj._meta.verbose_name.capitalize(), obj.title, what, modname),
                         admmsg)


# Moderate a single item
@login_required
@user_passes_test(lambda u: u.groups.filter(name='pgweb moderators').exists())
@transaction.atomic
@content_sources('style', "'unsafe-inline'")
def admin_moderate(request, objtype, objid):
    model = get_moderation_model(objtype)
    obj = get_object_or_404(model, pk=objid)

    initdata = {
        'oldmodstate': obj.modstate_string,
        'modstate': obj.modstate,
    }
    # Else deal with it as a form
    if request.method == 'POST':
        form = ModerationForm(request.POST, user=request.user, obj=obj, initial=initdata)
        if form.is_valid():
            # Ok, do something!
            modstate = int(form.cleaned_data['modstate'])
            modnote = form.cleaned_data['modnote']
            savefields = []

            if modstate == obj.modstate:
                # No change in moderation state, but did we want to send a message?
                if modnote:
                    _send_moderation_message(request, obj, None, modnote, None)
                    messages.info(request, "Moderation message sent, no state changed.")
                    return HttpResponseRedirect("/admin/pending/")
                else:
                    messages.warning(request, "Moderation state not changed and no moderation note added.")
                    return HttpResponseRedirect(".")

            # Ok, we have a moderation state change!
            if modstate == ModerationState.CREATED:
                # Returned to editing again (for two-state, this means de-moderated)
                _send_moderation_message(request,
                                         obj,
                                         "The {} with title {}\nhas been returned for further editing.\nPlease re-submit when you have adjusted it.".format(
                                             obj._meta.verbose_name,
                                             obj.title
                                         ),
                                         modnote,
                                         "returned")
            elif modstate == ModerationState.PENDING:
                # Pending moderation should never happen if we actually *change* the value
                messages.warning(request, "Cannot change state to 'pending moderation'")
                return HttpResponseRedirect(".")
            elif modstate == ModerationState.APPROVED:
                # Object requires two moderators
                if obj.twomoderators:
                    # Do we already have a moderator who approved it?
                    if not obj.firstmoderator:
                        # Nope. That means we record ourselves as the first moderator, and wait for a second moderator.
                        obj.firstmoderator = request.user
                        obj.save(update_fields=['firstmoderator', ])
                        messages.info(request, "{} approved, waiting for second moderator.".format(obj._meta.verbose_name))
                        return HttpResponseRedirect("/admin/pending")
                    elif obj.firstmoderator == request.user:
                        # Already approved by *us*
                        messages.warning(request, "{} was already approved by you, waiting for a second *different* moderator.".format(obj._meta.verbose_name))
                        return HttpResponseRedirect("/admin/pending")
                    # Else we fall through and approve it, as if only a single moderator was required

                _send_moderation_message(request,
                                         obj,
                                         "The {} with title {}\nhas been approved and is now published.".format(obj._meta.verbose_name, obj.title),
                                         modnote,
                                         "approved")

                # If there is a field called 'date', reset it to today so that it gets slotted into the correct place in lists
                if hasattr(obj, 'date') and isinstance(obj.date, date):
                    obj.date = date.today()
                    savefields.append('date')

                if hasattr(obj, 'on_approval'):
                    obj.on_approval(request)
            elif modstate == ModerationState.REJECTED:
                _send_moderation_message(request,
                                         obj,
                                         "The {} with title {}\nhas been rejected and is now deleted.".format(obj._meta.verbose_name, obj.title),
                                         modnote,
                                         "rejected")
                messages.info(request, "{} rejected and deleted".format(obj._meta.verbose_name))
                obj.send_notification = False
                obj.delete()
                return HttpResponseRedirect("/admin/pending")
            else:
                raise Exception("Can't happen.")

            if hasattr(obj, 'approved'):
                # This is a two-state one!
                obj.approved = (modstate == ModerationState.APPROVED)
                savefields.append('approved')
            else:
                # Three-state moderation
                obj.modstate = modstate
                savefields.append('modstate')

            if modstate != ModerationState.APPROVED and obj.twomoderators:
                # If changing to anything other than approved, we need to clear the moderator field, so things can start over
                obj.firstmoderator = None
                savefields.append('firstmoderator')

            # Suppress notifications as we're sending our own
            obj.send_notification = False
            obj.save(update_fields=savefields)
            messages.info(request, "Moderation state changed to {}".format(obj.modstate_string))
            return HttpResponseRedirect("/admin/pending/")
    else:
        form = ModerationForm(obj=obj, user=request.user, initial=initdata)

    return render(request, 'core/admin_moderation_form.html', {
        'obj': obj,
        'form': form,
        'app': obj._meta.app_label,
        'model': obj._meta.model_name,
        'itemtype': obj._meta.verbose_name,
        'itemtypeplural': obj._meta.verbose_name_plural,
        'notices': ModerationNotification.objects.filter(objectid=obj.id, objecttype=type(obj).__name__).order_by('date'),
        'previous': hasattr(obj, 'org') and type(obj).objects.filter(org=obj.org).exclude(id=obj.id).order_by('-id')[:10] or None,
        'object_fields': obj.get_moderation_preview_fields(),
    })


# Purge objects from varnish, for the admin pages
@login_required
@user_passes_test(lambda u: u.is_staff)
@user_passes_test(lambda u: u.groups.filter(name='varnish purgers').exists())
def admin_purge(request):
    if request.method == 'POST':
        url = request.POST['url']
        expr = request.POST['expr']
        template = request.POST['template']
        xkey = request.POST['xkey']
        l = len([_f for _f in [url, expr, template, xkey] if _f])
        if l == 0:
            # Nothing specified
            return HttpResponseRedirect('.')
        elif l > 1:
            messages.error(request, "Can only specify one of url, expression, template and xkey!")
            return HttpResponseRedirect('.')

        if url:
            varnish_purge(url)
        elif expr:
            varnish_purge_expr(expr)
        elif template:
            path = os.path.abspath(os.path.join(settings.PROJECT_ROOT, '../templates', template))
            if not os.path.isfile(path):
                messages.error(request, "Template {} does not exist!".format(template))
                return HttpResponseRedirect('.')
            # Calculate the xkey
            xkey = "pgwt_{}".format(hashlib.md5(template.encode('ascii')).hexdigest())
            varnish_purge_xkey(xkey)
        else:
            varnish_purge_xkey(xkey)

        messages.info(request, "Purge added.")
        return HttpResponseRedirect('.')

    # Fetch list of latest purges
    curs = connection.cursor()
    curs.execute("SELECT added, completed, consumer, CASE WHEN mode = 'K' THEN 'XKey' WHEN mode='P' THEN 'URL' ELSE 'Expression' END, expr FROM varnishqueue.queue q LEFT JOIN varnishqueue.consumers c ON c.consumerid=q.consumerid ORDER BY added DESC")
    latest = curs.fetchall()

    return render(request, 'core/admin_purge.html', {
        'latest_purges': latest,
    })


@csrf_exempt
def api_varnish_purge(request):
    if not request.META['REMOTE_ADDR'] in settings.VARNISH_PURGERS:
        raise PermissionDenied("Invalid client address")
    if request.method != 'POST':
        raise PermissionDenied("Can't use this way")
    n = int(request.POST['n'])
    curs = connection.cursor()
    for i in range(0, n):
        if 'p{0}'.format(i) in request.POST:
            curs.execute("SELECT varnish_purge_expr(%s)", (request.POST['p{0}'.format(i)], ))
        if 'x{0}'.format(i) in request.POST:
            curs.execute("SELECT varnish_purge_xkey(%s)", (request.POST['x{0}'.format(i)], ))

    return HttpResponse("Purged %s entries\n" % n)


# Merge two organisations
@login_required
@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def admin_mergeorg(request):
    if request.method == 'POST':
        form = MergeOrgsForm(data=request.POST)
        if form.is_valid():
            # Ok, try to actually merge organisations, by moving all objects
            # attached
            f = form.cleaned_data['merge_from']
            t = form.cleaned_data['merge_into']
            for e in f.event_set.all():
                e.org = t
                e.save()
            for n in f.newsarticle_set.all():
                n.org = t
                n.save()
            for p in f.product_set.all():
                p.org = t
                p.save()
            if hasattr(f, 'professionalservice'):
                p = f.professionalservice
                p.org = t
                p.save()
            for p in f.pug_set.all():
                p.org = t
                p.save()
            # Now that everything is moved, we can delete the organisation
            f.delete()

            messages.info(request, "Organisations merged")

            return HttpResponseRedirect("/admin/core/organisation/")
        # Else fall through to re-render form with errors
    else:
        form = MergeOrgsForm()

    return render(request, 'core/admin_mergeorg.html', {
        'form': form,
    })
