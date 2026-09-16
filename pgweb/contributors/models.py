import base64
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, When
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from pgweb.core.models import Organisation
from pgweb.core.text import ORGANISATION_HINT_TEXT
from pgweb.util.image import get_image_contenttype_from_bytes
from pgweb.util.moderation import TwostateModerateModel
from pgweb.util.fields import ImageBinaryField


def _profile_purge_url(user_id):
    # Purge URL for a user's profile page. The username is looked up
    # defensively because purge_urls can run during cascade deletes where the
    # User row is already gone.
    if not user_id:
        return None
    username = User.objects.filter(pk=user_id).values_list('username', flat=True).first()
    if username:
        return '/community/people/%s/$' % re.escape(username)
    return None


class ContributorType(models.Model):
    typename = models.CharField(max_length=32, null=False, blank=False)
    sortorder = models.IntegerField(null=False, default=100)
    extrainfo = models.TextField(null=True, blank=True)
    detailed = models.BooleanField(null=False, default=True)
    showemail = models.BooleanField(null=False, default=True)

    purge_urls = ('/community/contributors/$', )

    def __str__(self):
        return self.typename

    class Meta:
        ordering = ('sortorder',)


class Contributor(models.Model):
    ctype = models.ForeignKey(ContributorType,
                              on_delete=models.CASCADE,
                              verbose_name='Contributor Type', null=True, blank=True)
    firstname = models.CharField(max_length=100, null=False, blank=False)
    lastname = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    companyurl = models.URLField(max_length=100, null=True, blank=True, verbose_name='Company URL')
    location = models.CharField(max_length=100, null=True, blank=True)
    contribution = models.TextField(null=True, blank=True,
                                    help_text='Describe what you did in the PostgreSQL community')
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)

    send_notification = True

    def purge_urls(self):
        # A contributor edit shows up on the curated list, the all-people
        # list, the contributor's own profile page, and the badge pages that
        # list them as a holder.
        yield '/community/contributors/$'
        yield '/community/people/$'
        url = _profile_purge_url(self.user_id)
        if url:
            yield url
        if self.user_id:
            for badge_slug in Badgeholder.objects.filter(user_id=self.user_id).values_list('badge__slug', flat=True):
                yield '/community/badge/%s/$' % badge_slug

    def __str__(self):
        return "%s %s" % (self.firstname, self.lastname)

    class Meta:
        ordering = ('lastname', 'firstname',)


class BadgeManager(models.Manager):
    # imagedata is up to 1 MB per badge, so keep it out of the SELECT list
    # unless a caller asks for it. badge_image() fetches it explicitly,
    # and forms read it lazily for the single badge being edited.
    def get_queryset(self):
        return super().get_queryset().defer('imagedata')

    def with_has_image(self):
        # Annotate the image-fallback decision so views and templates can
        # avoid touching imagedata. The expression is evaluated SQL-side,
        # so the (up to 1 MB) value itself is never transferred.
        return self.get_queryset().annotate(has_image=Case(
            When(imagedata__gt=b'', then=True),
            default=False,
            output_field=models.BooleanField(),
        ))


class Badge(TwostateModerateModel):
    org = models.ForeignKey(Organisation, null=False, blank=False, verbose_name="Organisation", help_text=ORGANISATION_HINT_TEXT, on_delete=models.CASCADE)
    badge = models.CharField(max_length=32, null=False, blank=False, unique=True, help_text='Title of this badge, e.g. "PGConf.EU 2025 Speaker".')
    slug = models.SlugField(max_length=64, null=False, blank=False, unique=True, help_text='URL-friendly identifier for the badge page. Generated from the title when the badge is created, and kept fixed after that.')
    description = models.TextField(null=True, blank=True, help_text='What did the people do who contributed here?')
    url = models.URLField(max_length=100, null=True, blank=True, verbose_name='Contribution URL', help_text='URL for this contribution, e.g. the conference homepage. (Leave blank when there is no URL.)')
    imagedata = ImageBinaryField(max_length=1000000, resolution=(150, 150), auto_scale=True, blank=True, null=True, verbose_name="Image", help_text="Square image, will be auto-scaled to 150×150. JPEG or PNG, up to 1 MB. When left blank, the Slony logo will be used.")
    contact = models.CharField(max_length=100, null=True, blank=True, verbose_name='Contact address', help_text='Contact address (email, URL, other) for people who want to be added as badge holder')
    holders = models.ManyToManyField(User, through="Badgeholder", through_fields=("badge", "user"), blank=True)

    sortorder = models.IntegerField(null=True, blank=True, default=100)

    objects = BadgeManager()

    account_edit_suburl = 'badges'
    moderation_fields = ['org', 'badge', 'slug', 'description', 'url', 'image_preview', 'contact']
    send_notification = True

    def clean(self):
        # The slug is derived from the title, so an unusable or already-taken
        # title has to be rejected at submission time.
        base = slugify(self.badge)
        if not base:
            raise ValidationError({'badge': 'This title does not produce a usable URL slug.'})
        if not self.slug and Badge.objects.filter(slug=base).exists():
            raise ValidationError({'badge': 'This title produces a URL slug that is already in use.'})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.badge)
        super().save(*args, **kwargs)

    def purge_urls(self):
        # The badge's own page and image, plus the badge grid on the
        # all-people page. Holder profiles are not purged here; they get
        # refreshed when their holder rows are edited.
        yield '/community/badge/%s/$' % self.slug
        yield '/community/badge/%s/image/$' % self.slug
        yield '/community/people/$'

    @property
    def image_preview(self):
        # Rendered into the moderation preview. The image can't be served
        # from the badge image URL because that only serves approved badges,
        # so inline it as a data URI.
        if not self.imagedata:
            return '(no image)'
        return mark_safe('<img src="data:{0};base64,{1}" style="max-width:150px;max-height:150px" alt="">'.format(
            get_image_contenttype_from_bytes(self.imagedata[:8]),
            base64.b64encode(self.imagedata).decode('ascii'),
        ))

    def get_field_description(self, f):
        if f == 'image_preview':
            return 'Image'

    def verify_submitter(self, user):
        return (len(self.org.managers.filter(pk=user.pk)) == 1)

    def __str__(self):
        return self.badge

    @property
    def title(self):
        return self.badge

    class Meta:
        ordering = ('sortorder', 'badge')

    @classmethod
    def get_formclass(self):
        from pgweb.contributors.forms import BadgeForm
        return BadgeForm


class Badgeholder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)

    date_awarded = models.DateField(auto_now_add=True)
    date_retired = models.DateField(null=True, blank=True)
    awarded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="awarded_by")

    def purge_urls(self):
        # The badge page lists this holder, and the holder's profile page
        # shows this badge.
        yield '/community/badge/%s/$' % self.badge.slug
        url = _profile_purge_url(self.user_id)
        if url:
            yield url

    def __str__(self):
        label = f"{self.badge} {self.user.first_name} {self.user.last_name} ({self.user})"
        if self.date_retired:
            label += " (retired)"
        return label

    class Meta:
        ordering = ('badge__sortorder', 'badge', 'user__last_name', 'user__first_name')
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="unique_user_badge")
        ]
