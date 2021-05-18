from django.db.models.signals import pre_save, post_save, pre_delete
from django.db import models
from django.conf import settings

import difflib

from pgweb.util.middleware import get_current_user
from pgweb.util.misc import varnish_purge, varnish_purge_xkey
from pgweb.util.moderation import ModerationState
from pgweb.mailqueue.util import send_simple_mail


def _build_url(obj):
    if obj.id:
        return "%s/admin/%s/%s/%s/" % (
            settings.SITE_ROOT,
            obj._meta.app_label,
            obj._meta.model_name,
            obj.id,
        )
    else:
        return "%s/admin/%s/%s/" % (
            settings.SITE_ROOT,
            obj._meta.app_label,
            obj._meta.model_name,
        )


def _get_full_text_diff(obj, oldobj):
    fieldlist = _get_all_notification_fields(obj)
    if not fieldlist:
        return "This object does not know how to express ifself."

    s = "\n\n".join(["\n".join(
        [x for x in difflib.unified_diff(
            _get_attr_value(oldobj, n).splitlines(),
            _get_attr_value(obj, n).splitlines(),
            n=1,
            lineterm='',
            fromfile=n,
            tofile=n,
        ) if not x.startswith('@@')]
    ) for n in fieldlist if _get_attr_value(oldobj, n) != _get_attr_value(obj, n)])
    if not s:
        return None
    return s


def _get_all_notification_fields(obj):
    if hasattr(obj, 'notify_fields'):
        return obj.notify_fields
    else:
        # Include all field names except specified ones,
        # that are local to this model (not auto created)
        return [f.name for f in obj._meta.get_fields() if f.name not in ('approved', 'modstate', 'submitter', 'id', ) and not f.auto_created]


def _get_attr_value(obj, fieldname):
    # see if this is a Many-to-many field. If yes, we want to print
    # it out as a pretty list
    if isinstance(obj._meta.get_field(fieldname), models.ManyToManyField):
        # XXX: Changes to ManyToMany fields can't be tracked here :(
        #      For now, we have no good way to deal with it so, well, don't.
        #      (trying to get the value will return None for it)
        return ''

    # Return the value, or an empty string if it's NULL (migrated records)
    return str(getattr(obj, fieldname)) or ''


def _get_full_text_representation(obj):
    fieldlist = _get_all_notification_fields(obj)
    if not fieldlist:
        return "This object does not know how to express itself."

    return "\n".join(['%s: %s' % (n, _get_attr_value(obj, n)) for n in fieldlist])


def _get_notification_text(obj):
    try:
        oldobj = obj.__class__.objects.get(pk=obj.pk)
    except obj.DoesNotExist:
        return ('A new {0} has been added'.format(obj._meta.verbose_name),
                _get_full_text_representation(obj))

    if hasattr(obj, 'approved') or hasattr(obj, 'modstate'):
            # This object has the capability to do approving. Apply the following logic:
            # 1. If object was unapproved, and is still unapproved, don't send notification
            # 2. If object was unapproved, and is now approved, send "object approved" notification
            # 3. If object was approved, and is no longer approved, send "object unapproved" notification
            # 4. (FIXME: configurable?) If object was approved and is still approved, send changes notification

        if hasattr(obj, 'approved'):
            approved = obj.approved
            oldapproved = oldobj.approved
        else:
            approved = obj.modstate != ModerationState.CREATED
            oldapproved = oldobj.modstate != ModerationState.CREATED

        if not approved:
            if not oldapproved:
                # Was approved, still approved -> no notification
                return (None, None)
            # From approved to unapproved
            return ('{0} id {1} ({2}) has been unapproved'.format(obj._meta.verbose_name, obj.id, str(obj)),
                    _get_full_text_representation(obj))
        else:
            if not oldapproved:
                # Object went from unapproved to approved
                return ('{0} id {1} ({2}) has been approved'.format(obj._meta.verbose_name, obj.id, str(obj)),
                        _get_full_text_representation(obj))
            # Object contents have changed. Generate a diff!
        diff = _get_full_text_diff(obj, oldobj)
        if not diff:
            return (None, None)
        return ('{0} id {1} ({2}) has been modified'.format(obj._meta.verbose_name, obj.id, str(obj)),
                'The following fields have been modified:\n\n%s' % diff)
    else:
        # If there is no approved field, but send_notifications was set
        # to True, we notify on all changes.
        diff = _get_full_text_diff(obj, oldobj)
        if not diff:
            return (None, None)
        return ('{0} id {1} ({2}) has been modified'.format(obj._meta.verbose_name, obj.id, str(obj)),
                'The following fields have been modified:\n\n%s' % diff)


def my_pre_save_handler(sender, **kwargs):
    instance = kwargs['instance']
    if getattr(instance, 'send_notification', False) and get_current_user():
        (subj, cont) = _get_notification_text(instance)
        if cont:
            cont = _build_url(instance) + "\n\n" + cont
            send_simple_mail(settings.NOTIFICATION_FROM,
                             settings.NOTIFICATION_EMAIL,
                             "%s by %s" % (subj, get_current_user()),
                             cont)


def my_pre_delete_handler(sender, **kwargs):
    instance = kwargs['instance']
    if getattr(instance, 'send_notification', False) and get_current_user():
        send_simple_mail(settings.NOTIFICATION_FROM,
                         settings.NOTIFICATION_EMAIL,
                         "%s id %s has been deleted by %s" % (
                             instance._meta.verbose_name,
                             instance.id,
                             get_current_user()),
                         _get_full_text_representation(instance))


def my_post_save_handler(sender, **kwargs):
    instance = kwargs['instance']
    if hasattr(instance, 'purge_urls'):
        if callable(instance.purge_urls):
            purgelist = instance.purge_urls()
        else:
            purgelist = instance.purge_urls
        list(map(varnish_purge, purgelist))
    if hasattr(instance, 'purge_xkeys'):
        if callable(instance.purge_xkeys):
            purgelist = instance.purge_xkeys()
        else:
            purgelist = instance.purge_xkeys
        list(map(varnish_purge_xkey, purgelist))


def register_basic_signal_handlers():
    pre_save.connect(my_pre_save_handler)
    pre_delete.connect(my_pre_delete_handler)
    post_save.connect(my_post_save_handler)
