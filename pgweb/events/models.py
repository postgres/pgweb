from django.db import models
from django.contrib.auth.models import User
from datetime import date
from pgweb.util.bases import PgModel

from core.models import Country, Organisation

class Event(models.Model, PgModel):
	approved = models.BooleanField(null=False, blank=False, default=False)

	org = models.ForeignKey(Organisation, null=False, blank=False)
	title = models.CharField(max_length=100, null=False, blank=False)
	city = models.CharField(max_length=50, null=False, blank=False)
	state = models.CharField(max_length=50, null=False, blank=True)	
	country = models.ForeignKey(Country, null=False, blank=False)
	
	training = models.BooleanField(null=False, blank=False, default=False)
	startdate = models.DateField(null=False, blank=False)
	enddate = models.DateField(null=False, blank=False)
	
	summary = models.TextField(blank=False, null=False)
	details = models.TextField(blank=False, null=False)
	
	send_notification = True
	markdown_fields = ('details', )
	
	def purge_urls(self):
		yield '/about/event/%s/' % self.pk
		yield '/about/eventarchive/'
		yield 'events.rss'
		# FIXME: when to expire the front page?
		yield '/$'

	def __unicode__(self):
		return "%s: %s" % (self.startdate, self.title)

	def verify_submitter(self, user):
		return (len(self.org.managers.filter(pk=user.pk)) == 1)

	@property
	def has_organisation(self):
		mgrs = self.org.managers.all()
		if len(mgrs) == 1:
			if mgrs[0].pk == 0:
				return False # Migration organisation
			else:
				return True # Has an actual organisation
		return False # Has no organisastion at all

	@property
	def displaydate(self):
		if self.startdate == self.enddate:
			return self.startdate
		else:
			return "%s &ndash; %s" % (self.startdate, self.enddate)
	
	@property
	def locationstring(self):
		if self.state:
			return "%s, %s, %s" % (self.city, self.state, self.country)
		else:
			return "%s, %s" % (self.city, self.country)

	class Meta:
		ordering = ('-startdate','-enddate',)

