from django.db import models

from pgweb.core.models import Country, Language, Organisation
from pgweb.util.moderation import TwostateModerateModel


class Event(TwostateModerateModel):
    org = models.ForeignKey(Organisation, null=False, blank=False, verbose_name="Organisation", help_text="If no organisations are listed, please check the <a href=\"/account/orglist/\">organisation list</a> and contact the organisation manager or <a href=\"mailto:webmaster@postgresql.org\">webmaster@postgresql.org</a> if none are listed.", on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=False, blank=False)
    isonline = models.BooleanField(null=False, default=False, verbose_name="Online event")
    city = models.CharField(max_length=50, null=False, blank=True)
    state = models.CharField(max_length=50, null=False, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, null=True, blank=True, default='eng', help_text="Primary language for event. When multiple languages, specify this in the event description", on_delete=models.CASCADE)

    badged = models.BooleanField(null=False, blank=False, default=False, verbose_name='Community event', help_text='Choose "Community event" if this is a community recognized event following the <a href="/community/recognition/#conferences" target="_blank" rel="noopener">community event guidelines</a>.')
    description_for_badged = models.TextField(blank=True, null=True, verbose_name='Description for community event', help_text='DEPRECRATED: This was used in the beginning of community events to collect additional information.')
    startdate = models.DateField(null=False, blank=False, verbose_name="Start date")
    enddate = models.DateField(null=False, blank=False, verbose_name="End date")

    summary = models.TextField(blank=False, null=False, help_text="A short introduction (shown on the events listing page)")
    details = models.TextField(blank=False, null=False, help_text="Complete event description")

    account_edit_suburl = 'events'
    markdown_fields = ('details', 'summary', )
    moderation_fields = ['org', 'title', 'isonline', 'city', 'state', 'country', 'language', 'badged', 'description_for_badged', 'startdate', 'enddate', 'summary', 'details']

    def purge_urls(self):
        yield '/about/event/%s/' % self.pk
        yield '/about/events/'
        yield '/events.rss'
        # FIXME: when to expire the front page?
        yield '/$'

    def __str__(self):
        return "%s: %s" % (self.startdate, self.title)

    def verify_submitter(self, user):
        return (len(self.org.managers.filter(pk=user.pk)) == 1)

    @property
    def has_organisation(self):
        mgrs = self.org.managers.all()
        if len(mgrs) == 1:
            if mgrs[0].pk == 0:
                return False  # Migration organisation
            else:
                return True  # Has an actual organisation
        elif len(mgrs) > 1:
            # More than one manager means it must be new
            return True
        return False  # Has no organisastion at all

    @property
    def displaydate(self):
        if self.startdate == self.enddate:
            return self.startdate
        else:
            return "%s &ndash; %s" % (self.startdate, self.enddate)

    @property
    def locationstring(self):
        if self.isonline:
            return "online"
        elif self.state:
            return "%s, %s, %s" % (self.city, self.state, self.country)
        else:
            return "%s, %s" % (self.city, self.country)

    class Meta:
        ordering = ('-startdate', '-enddate', )

    @classmethod
    def get_formclass(self):
        from pgweb.events.forms import EventForm
        return EventForm
