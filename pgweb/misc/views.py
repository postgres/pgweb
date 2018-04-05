from pgweb.util.decorators import login_required
from django.http import HttpResponse
from django.db import connection
from django.conf import settings

import os

from pgweb.util.contexts import render_pgweb
from pgweb.util.helpers import template_to_string
from pgweb.util.misc import send_template_mail

from pgweb.core.models import Version

from forms import SubmitBugForm

@login_required
def submitbug(request):
	if request.method == 'POST':
		form = SubmitBugForm(request.POST)
		if form.is_valid():
			c = connection.cursor()
			c.execute("SELECT nextval('bug_id_seq')")
			bugid = c.fetchall()[0][0]

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
			)

			return render_pgweb(request, 'support', 'misc/bug_completed.html', {
				'bugid': bugid,
			})
	else:
		form = SubmitBugForm(initial={
			'name': '%s %s' % (request.user.first_name, request.user.last_name),
			'email': request.user.email,
		})

	versions = Version.objects.filter(supported=True)

	return render_pgweb(request, 'support', 'base/form.html', {
		'form': form,
		'formitemtype': 'bug report',
		'operation': 'Submit',
		'form_intro': template_to_string('misc/bug_header.html', {
			'supportedversions': versions,
		}),
		'savebutton': 'Create report and send email',
	})


# A crash testing URL. If the file /tmp/crashtest exists, raise a http 500
# error. Otherwise, just return a fixed text response
def crashtest(request):
	if os.path.exists('/tmp/crashtest'):
		raise Exception('This is a manual test of a crash!')
	else:
		return HttpResponse('Crash testing disabled', content_type='text/plain')
