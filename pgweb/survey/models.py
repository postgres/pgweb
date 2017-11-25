from django.db import models

# internal text/value object
class SurveyQuestion(object):
	def __init__(self, value, text):
		self.value = value
		self.text = text
class SurveyAnswerValues(object):
	def __init__(self, option, votes, votespercent):
		self.option = option
		self.votes = votes
		self.votespercent = votespercent

class Survey(models.Model):
	question = models.CharField(max_length=500, null=False, blank=False)
	opt1 = models.CharField(max_length=500, null=False, blank=False)
	opt2 = models.CharField(max_length=500, null=False, blank=False)
	opt3 = models.CharField(max_length=500, null=False, blank=True)
	opt4 = models.CharField(max_length=500, null=False, blank=True)
	opt5 = models.CharField(max_length=500, null=False, blank=True)
	opt6 = models.CharField(max_length=500, null=False, blank=True)
	opt7 = models.CharField(max_length=500, null=False, blank=True)
	opt8 = models.CharField(max_length=500, null=False, blank=True)
	posted = models.DateTimeField(null=False, auto_now_add=True)
	current = models.BooleanField(null=False, default=False)

	purge_urls = ('/community/survey', '/community/$')

	def __unicode__(self):
		return self.question

	@property
	def questions(self):
		for i in range (1,9):
			v = getattr(self, "opt%s" % i)
			if not v: break
			yield SurveyQuestion(i, v)

	@property
	def answers(self):
		if not hasattr(self, "_answers"):
			self._answers = SurveyAnswer.objects.get_or_create(survey=self)[0]
		return self._answers

	@property
	def completeanswers(self):
		for a in self._get_complete_answers():
			yield SurveyAnswerValues(a[0], a[1], self.totalvotes>0 and (100*a[1]/self.totalvotes) or 0)

	@property
	def totalvotes(self):
		if not hasattr(self,"_totalvotes"):
			self._totalvotes = 0
			for a in self._get_complete_answers():
				self._totalvotes = self._totalvotes + a[1]
		return self._totalvotes

	def _get_complete_answers(self):
		for i in range(1,9):
			q = getattr(self, "opt%s" % i)
			if not q: break
			n = getattr(self.answers, "tot%s" % i)
			yield (q,n)

	def save(self):
		# Make sure only one survey at a time can be the current one
		# (there may be some small race conditions here, but the likelyhood
		# that two admins are editing the surveys at the same time...)
		if self.current:
			previous = Survey.objects.filter(current=True)
			for p in previous:
				if not p == self:
					p.current = False
					p.save() # primary key check avoids recursion

		# Now that we've made any previously current ones non-current, we are
		# free to save this one.
		super(Survey, self).save()

class SurveyAnswer(models.Model):
	survey = models.OneToOneField(Survey, null=False, blank=False, primary_key=True)
	tot1 = models.IntegerField(null=False, default=0)
	tot2 = models.IntegerField(null=False, default=0)
	tot3 = models.IntegerField(null=False, default=0)
	tot4 = models.IntegerField(null=False, default=0)
	tot5 = models.IntegerField(null=False, default=0)
	tot6 = models.IntegerField(null=False, default=0)
	tot7 = models.IntegerField(null=False, default=0)
	tot8 = models.IntegerField(null=False, default=0)

	purge_urls = ('/community/survey', )

class SurveyLock(models.Model):
	ipaddr = models.GenericIPAddressField(null=False, blank=False)
	time = models.DateTimeField(null=False, auto_now_add=True)
