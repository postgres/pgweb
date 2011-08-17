from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.db import connection
from django.template.defaultfilters import slugify

from pgweb.util.contexts import NavContext
from pgweb.util.misc import get_client_ip
from pgweb.util.helpers import HttpServerError

from models import Survey, SurveyAnswer, SurveyLock

def results(request, surveyid, junk=None):
	survey = get_object_or_404(Survey, pk=surveyid)
	surveylist = Survey.objects.all().order_by('-posted')

	return render_to_response('survey/results.html', {
		'survey': survey,
		'surveylist': surveylist,
	}, NavContext(request, 'community'))

def vote(request, surveyid):
	surv = get_object_or_404(Survey, pk=surveyid)

	# Check that we have a valid answer number
	try:
		ansnum = int(request.POST['answer'])
		if ansnum < 1 or ansnum > 8:
			return HttpServerError("Invalid answer")
	except:
		# When no answer is given, redirect to results instead
		return HttpResponseRedirect("/community/survey/%s-%s" % (surv.id, slugify(surv.question)))
	attrname = "tot%s" % ansnum

	# Do IP based locking...
	addr = get_client_ip(request)

	# Clean out any old junk
	curs = connection.cursor()
	curs.execute("DELETE FROM survey_surveylock WHERE (\"time\" + '15 minutes') < now()")

	# Check if we are locked
	lock = SurveyLock.objects.filter(ipaddr=addr)
	if len(lock) > 0:
		return HttpServerError("Too many requests from your IP in the past 15 minutes")

	# Generate a new lock item, and store it
	lock = SurveyLock(ipaddr=addr)
	lock.save()

	answers = SurveyAnswer.objects.get_or_create(survey=surv)[0]
	setattr(answers, attrname, getattr(answers, attrname)+1)
	answers.save()

	return HttpResponseRedirect("/community/survey/%s/" % surveyid)

