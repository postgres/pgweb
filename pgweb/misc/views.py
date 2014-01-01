from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.conf import settings

import os

from pgweb.util.contexts import NavContext
from pgweb.util.helpers import template_to_string
from pgweb.util.misc import send_template_mail

from pgweb.core.models import Version

from forms import SubmitBugForm

@csrf_exempt
def submitbug(request):
	if request.method == 'POST':
		form = SubmitBugForm(request.POST)
		if form.is_valid():
			c = connection.cursor()
			c.execute("SELECT nextval('bug_id_seq')")
			bugid = c.fetchall()[0][0]

			send_template_mail(
				form.cleaned_data['email'],
				settings.BUGREPORT_EMAIL,
				'BUG #%s: %s' % (bugid, form.cleaned_data['shortdesc']),
				'misc/bugmail.txt',
				{
					'bugid': bugid,
					'bug': form.cleaned_data,
				}
			)

			return render_to_response('misc/bug_completed.html', {
				'bugid': bugid,
			}, NavContext(request, 'support'))
	else:
		form = SubmitBugForm()

	versions = Version.objects.filter(supported=True)

	return render_to_response('base/form.html', {
		'form': form,
		'formitemtype': 'bug report',
		'operation': 'Submit',
		'nocsrf': True,
		'form_intro': template_to_string('misc/bug_header.html', {
			'supportedversions': versions,
		}),
	}, NavContext(request, 'support'))


# A crash testing URL. If the file /tmp/crashtest exists, raise a http 500
# error. Otherwise, just return a fixed text response
def crashtest(request):
	if os.path.exists('/tmp/crashtest'):
		raise Exception('This is a manual test of a crash!')
	else:
		return HttpResponse('Crash testing disabled', content_type='text/plain')
