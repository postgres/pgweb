from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect
from django.db import connection

from pgweb.util.contexts import NavContext

from models import Survey, SurveyAnswer, SurveyLock

def results(request, surveyid, junk=None):
	survey = get_object_or_404(Survey, pk=surveyid)
	surveylist = Survey.objects.all()

	return render_to_response('survey/results.html', {
		'survey': survey,
		'surveylist': surveylist,
	}, NavContext(request, 'community'))

def vote(request, surveyid):
	# Check that we have a valid answer number
	try:
		ansnum = int(request.POST['answer'])
		if ansnum < 1 or ansnum > 8:
			return HttpResponseServerError("Invalid answer")
	except:
		return HttpResponseServerError("Unable to determine answer")
	attrname = "tot%s" % ansnum

	# Do IP based locking...
	try:
		addr = request.META.get('REMOTE_ADDR')
		if addr == None or addr == "":
			raise Exception()
	except:
		return HttpResponseServerError("Unable to determine client IP address")

	# Clean out any old junk
	curs = connection.cursor()
	curs.execute("DELETE FROM survey_surveylock WHERE (\"time\" + '15 minutes') < now()")

	# Check if we are locked
	lock = SurveyLock.objects.filter(ipaddr=addr)
	if len(lock) > 0:
		return HttpResponseServerError("Too many requests from your IP in the past 15 minutes")

	# Generate a new lock item, and store it
	lock = SurveyLock(ipaddr=addr)
	lock.save()

	# Only now do we bother actually finding out if the survey exists...
	surv = get_object_or_404(Survey, pk=surveyid)
	answers = SurveyAnswer.objects.get_or_create(survey=surv)[0]
	setattr(answers, attrname, getattr(answers, attrname)+1)
	answers.save()

	return HttpResponseRedirect("/community/survey/%s/" % ansnum)

