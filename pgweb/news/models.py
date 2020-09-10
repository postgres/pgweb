from django.db import models
from datetime import date
from pgweb.core.models import Organisation
from pgweb.util.moderation import TristateModerateModel, ModerationState, TwoModeratorsMixin


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
    org = models.ForeignKey(Organisation, null=False, blank=False, verbose_name="Organisation", help_text="If no organisations are listed, please check the <a href=\"/account/orglist/\">organisation list</a> and contact the organisation manager or <a href=\"mailto:webmaster@postgresql.org\">webmaster@postgresql.org</a> if none are listed.", on_delete=models.CASCADE)
    date = models.DateField(null=False, blank=False, default=date.today)
    title = models.CharField(max_length=200, null=False, blank=False)
    content = models.TextField(null=False, blank=False)
    tweeted = models.BooleanField(null=False, blank=False, default=False)
    tags = models.ManyToManyField(NewsTag, blank=False, help_text="Select the tags appropriate for this post")

    account_edit_suburl = 'news'
    markdown_fields = ('content',)
    moderation_fields = ('org', 'date', 'title', 'content', 'taglist')
    preview_fields = ('title', 'content', 'taglist')
    extramodnotice = "In particular, note that news articles will be sent by email to subscribers, and therefor cannot be recalled in any way once sent."

    def purge_urls(self):
        yield '/about/news/%s/' % self.pk
        yield '/about/newsarchive/'
        yield '/news.rss'
        yield '/news/.*.rss'
        # FIXME: when to expire the front page?
        yield '/$'

    def __str__(self):
        return "%s: %s" % (self.date, self.title)

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
