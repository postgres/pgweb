from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.db import connection
from email.mime.text import MIMEText
from django.conf import settings

from pgweb.util.contexts import NavContext
from pgweb.util.helpers import template_to_string
from pgweb.util.misc import sendmail

from pgweb.core.models import Version

from forms import *

def submitbug(request):
	if request.method == 'POST':
		form = SubmitBugForm(request.POST)
		if form.is_valid():
			c = connection.cursor()
			c.execute("SELECT nextval('bug_id_seq')")
			bugid = c.fetchall()[0][0]

			msg = MIMEText(
				template_to_string('misc/bugmail.txt', {
					'bugid': bugid,
					'bug': form.cleaned_data,
				}),
				_charset='utf-8')
			msg['Subject'] = 'BUG #%s: %s' % (bugid, form.cleaned_data['shortdesc'])
			msg['To'] = settings.BUGREPORT_EMAIL
			msg['From'] = form.cleaned_data['email']
			sendmail(msg)

			return render_to_response('misc/bug_completed.html', {
				'bugid': bugid,
			}, NavContext(request, 'support'))
	else:
		form = SubmitBugForm()

	versions = Version.objects.all()

	return render_to_response('base/form.html', {
		'form': form,
		'formitemtype': 'Bug report',
		'form_intro': template_to_string('misc/bug_header.html', {
			'supportedversions': versions,
		}),
	}, NavContext(request, 'support'))

