from pgweb.util.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection, transaction
from django.shortcuts import get_object_or_404
from django.conf import settings

import os
import time
import hashlib

from pgweb.util.contexts import render_pgweb
from pgweb.util.helpers import template_to_string
from pgweb.util.misc import send_template_mail

from pgweb.core.models import Version
from pgweb.misc.models import BugIdMap

from forms import SubmitBugForm


def _make_bugs_messageid(bugid):
    return "<{0}-{1}@postgresql.org>".format(
        bugid,
        hashlib.md5("{0}-{1}".format(os.getpid(), time.time())).hexdigest()[:16],
    )


@login_required
def submitbug(request):
    if request.method == 'POST':
        form = SubmitBugForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                c = connection.cursor()
                c.execute("SELECT nextval('bug_id_seq')")
                bugid = c.fetchall()[0][0]

                messageid = _make_bugs_messageid(bugid)

                BugIdMap(id=bugid, messageid=messageid.strip('<>')).save()

                send_template_mail(
                    settings.BUGREPORT_NOREPLY_EMAIL,
                    settings.BUGREPORT_EMAIL,
                    'BUG #%s: %s' % (bugid, form.cleaned_data['shortdesc']),
                    'misc/bugmail.txt',
                    {
                        'bugid': bugid,
                        'bug': form.cleaned_data,
                    },
                    usergenerated=True,
                    cc=form.cleaned_data['email'],
                    replyto='%s, %s' % (form.cleaned_data['email'], settings.BUGREPORT_EMAIL),
                    sendername="PG Bug reporting form",
                    messageid=messageid,
                )

                return HttpResponseRedirect("/account/submitbug/{0}/".format(bugid))
    else:
        form = SubmitBugForm(initial={
            'name': '%s %s' % (request.user.first_name, request.user.last_name),
            'email': request.user.email,
        })

    versions = Version.objects.filter(supported=True)

    return render_pgweb(request, 'support', 'base/form.html', {
        'form': form,
        'formitemtype': 'bug report',
        'formtitle': 'Submit Bug Report <i class="fas fa-bug"></i>',
        'operation': 'Submit',
        'form_intro': template_to_string('misc/bug_header.html', {
            'supportedversions': versions,
        }),
        'savebutton': 'Submit and Send Email',
    })


@login_required
def submitbug_done(request, bugid):
    return render_pgweb(request, 'support', 'misc/bug_completed.html', {
        'bugid': bugid,
    })


def bugs_redir(request, bugid):
    r = get_object_or_404(BugIdMap, id=bugid)

    return HttpResponseRedirect("{0}/message-id/{1}".format(settings.SITE_ROOT, r.messageid))


# A crash testing URL. If the file /tmp/crashtest exists, raise a http 500
# error. Otherwise, just return a fixed text response
def crashtest(request):
    if os.path.exists('/tmp/crashtest'):
        raise Exception('This is a manual test of a crash!')
    else:
        return HttpResponse('Crash testing disabled', content_type='text/plain')
