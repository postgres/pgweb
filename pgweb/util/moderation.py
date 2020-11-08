from django.db import models
from django.contrib.auth.models import User

import datetime

from pgweb.util.markup import pgmarkdown


class ModerateModel(models.Model):
    def _get_field_data(self, k):
        val = getattr(self, k)
        yield k

        try:
            d = self.get_field_description(k)
        except Exception:
            d = None

        if d:
            yield d.capitalize()
        else:
            try:
                yield self._meta.get_field(k).verbose_name.capitalize()
            except Exception:
                yield k.capitalize()

        yield val

        if k in getattr(self, 'rendered_preview_fields', []):
            yield self.render_preview_field(k, val)
        elif k in getattr(self, 'markdown_fields', []):
            yield pgmarkdown(val)
        else:
            yield None

        if k == 'date' and isinstance(val, datetime.date):
            yield "Will be reset to today's date when this {} is approved".format(self._meta.verbose_name)
        else:
            yield None

    def get_preview_fields(self):
        if getattr(self, 'preview_fields', []):
            return [list(self._get_field_data(k)) for k in self.preview_fields]
        return self.get_moderation_preview_fields()

    def get_moderation_preview_fields(self):
        return [list(self._get_field_data(k)) for k in self.moderation_fields]

    class Meta:
        abstract = True

    @property
    def block_edit(self):
        return False

    @property
    def twomoderators(self):
        return hasattr(self, 'firstmoderator')

    def twomoderators_string(self):
        return None


class ModerationState(object):
    CREATED = 0
    PENDING = 1
    APPROVED = 2
    REJECTED = -1  # Never stored, so not available as a choice

    CHOICES = (
        (CREATED, 'Created (submitter edits)'),
        (PENDING, 'Pending moderation'),
        (APPROVED, 'Approved and published'),
    )

    @classmethod
    def get_string(cls, modstate):
        return next(filter(lambda x: x[0] == modstate, cls.CHOICES))[1]


class TristateModerateModel(ModerateModel):
    modstate = models.IntegerField(null=False, blank=False, default=0, choices=ModerationState.CHOICES,
                                   verbose_name="Moderation state")

    send_notification = True
    send_m2m_notification = True

    class Meta:
        abstract = True

    @property
    def modstate_string(self):
        return ModerationState.get_string(self.modstate)

    @property
    def is_approved(self):
        return self.modstate == ModerationState.APPROVED


class TwostateModerateModel(ModerateModel):
    approved = models.BooleanField(null=False, blank=False, default=False)

    send_notification = True
    send_m2m_notification = True

    class Meta:
        abstract = True

    @property
    def modstate_string(self):
        return self.approved and 'Approved' or 'Created/Pending'

    @property
    def modstate(self):
        return self.approved and ModerationState.APPROVED or ModerationState.CREATED

    @property
    def is_approved(self):
        return self.approved


class TwoModeratorsMixin(models.Model):
    firstmoderator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True

    def twomoderators_string(self):
        if self.firstmoderator:
            return "Already approved by {}, waiting for second moderator".format(self.firstmoderator)
        return "Requires two moderators, not approved by anybody yet"


# Pending moderation requests (including URLs for the admin interface))
def _get_unapproved_list(objecttype):
    if hasattr(objecttype, 'approved'):
        objects = objecttype.objects.filter(approved=False)
    else:
        objects = objecttype.objects.filter(modstate=ModerationState.PENDING)
    if not len(objects):
        return None
    return {
        'name': objects[0]._meta.verbose_name_plural,
        'entries': [
            {
                'url': '/admin/_moderate/%s/%s/' % (x._meta.model_name, x.pk),
                'title': str(x),
                'twomoderators': x.twomoderators_string(),
            } for x in objects]
    }


def _modclasses():
    from pgweb.news.models import NewsArticle
    from pgweb.events.models import Event
    from pgweb.core.models import Organisation
    from pgweb.downloads.models import Product
    from pgweb.profserv.models import ProfessionalService
    return [NewsArticle, Event, Organisation, Product, ProfessionalService]


def get_all_pending_moderations():
    applist = [_get_unapproved_list(c) for c in _modclasses()]
    return [x for x in applist if x]


def get_moderation_model(modelname):
    return next((c for c in _modclasses() if c._meta.model_name == modelname))


def get_moderation_model_from_suburl(suburl):
    return next((c for c in _modclasses() if c.account_edit_suburl == suburl))
