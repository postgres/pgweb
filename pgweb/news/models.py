from django.db import models
from datetime import date
from pgweb.core.models import Organisation, OrganisationEmail
from pgweb.core.text import ORGANISATION_HINT_TEXT
from pgweb.util.moderation import TristateModerateModel, ModerationState, TwoModeratorsMixin
from django.template.defaultfilters import slugify

from .util import send_news_email, render_news_template, embed_images_in_html


class NewsTag(models.Model):
    urlname = models.CharField(max_length=20, null=False, blank=False, unique=True)
    name = models.CharField(max_length=32, null=False, blank=False)
    description = models.CharField(max_length=200, null=False, blank=False)
    allowed_orgs = models.ManyToManyField(Organisation, blank=True,
                                          help_text="Organisations allowed to use this tag")
    sortkey = models.IntegerField(null=False, blank=False, default=100)

    def purge_urls(self):
        yield '/about/news/taglist.json/'

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('sortkey', 'urlname', )


class NewsArticle(TwoModeratorsMixin, TristateModerateModel):
    org = models.ForeignKey(Organisation, null=False, blank=False, verbose_name="Organisation", help_text=ORGANISATION_HINT_TEXT, on_delete=models.CASCADE)
    email = models.ForeignKey(OrganisationEmail, null=True, blank=True, verbose_name="Reply email", help_text="Pick a confirmed email associated with the organisation. This will be used as the reply address of posted news.", on_delete=models.PROTECT)
    date = models.DateField(null=False, blank=False, default=date.today, db_index=True)
    title = models.CharField(max_length=200, null=False, blank=False)
    content = models.TextField(null=False, blank=False)
    tweeted = models.BooleanField(null=False, blank=False, default=False)
    tags = models.ManyToManyField(NewsTag, blank=False, help_text="Select the tags appropriate for this post")

    account_edit_suburl = 'news'
    markdown_fields = ('content',)
    moderation_fields = ('permanenturl', 'org', 'sentfrom', 'email', 'date', 'title', 'content', 'taglist')
    preview_fields = ('title', 'sentfrom', 'email', 'content', 'taglist')
    notify_fields = ('org', 'email', 'date', 'title', 'content', 'tags')
    rendered_preview_fields = ('content', )
    extramodnotice = "In particular, note that news articles will be sent by email to subscribers, and therefor cannot be recalled in any way once sent."

    def purge_urls(self):
        yield '/about/news/%s/' % self.pk
        yield '/about/news/.*-%s/' % self.pk
        yield '/about/newsarchive/'
        yield '/news.rss'
        yield '/news/.*.rss'
        # FIXME: when to expire the front page?
        yield '/$'

    def __str__(self):
        return "%s: %s" % (self.date, self.title)

    @property
    def permanenturl(self):
        return '/about/news/{}-{}/'.format(slugify(self.title), self.id)

    def verify_submitter(self, user):
        return (len(self.org.managers.filter(pk=user.pk)) == 1)

    def is_migrated(self):
        if self.org.pk == 0:
            return True
        return False

    @property
    def taglist(self):
        return ", ".join([t.name for t in self.tags.all()])

    @property
    def sentfrom(self):
        return self.org.fromnameoverride if self.org.fromnameoverride else '{} via PostgreSQL Announce'.format(self.org.name)

    @property
    def displaydate(self):
        return self.date.strftime("%Y-%m-%d")

    class Meta:
        ordering = ('-date',)

    @classmethod
    def get_formclass(self):
        from pgweb.news.forms import NewsArticleForm
        return NewsArticleForm

    @property
    def block_edit(self):
        # Don't allow editing of news articles that have been published
        return self.modstate in (ModerationState.PENDING, ModerationState.APPROVED)

    def on_approval(self, request):
        send_news_email(self)

    def render_preview_field(self, fieldname, val):
        if fieldname == 'content':
            html, attachments = render_news_template(self)
            return embed_images_in_html(html, attachments)

    def get_field_description(self, f):
        if f == 'title':
            return 'Title/subject'
        elif f == 'sentfrom':
            return 'Sent from'
        elif f == 'email':
            return 'Direct replies to'
        elif f == 'taglist':
            return 'List of tags'
        elif f == 'content':
            return 'Content preview'
        elif f == 'permanenturl':
            return 'Permanent URL'
