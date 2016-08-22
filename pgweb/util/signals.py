from django.db.models.signals import pre_save, post_save, pre_delete
from django.db import models
from django.conf import settings

import difflib

from pgweb.util.middleware import get_current_user
from pgweb.util.misc import varnish_purge
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

	s = "\n\n".join(["\n".join(filter(lambda x: not x.startswith('@@'),
		difflib.unified_diff(
			_get_attr_value(oldobj, n).splitlines(),
			_get_attr_value(obj, n).splitlines(),
			n=1,
			lineterm='',
			fromfile=n,
			tofile=n,
			))
	) for n in fieldlist if _get_attr_value(oldobj, n) != _get_attr_value(obj, n)])
	if not s: return None
	return s

def _get_all_notification_fields(obj):
	if hasattr(obj, 'notify_fields'):
		return obj.notify_fields
	else:
		# Include all field names except specified ones,
		# that are "direct" (by get_field_by_name()[2])
		return [n for n in obj._meta.get_all_field_names() if not n in ('approved', 'submitter', 'id', ) and obj._meta.get_field_by_name(n)[2]]

def _get_attr_value(obj, fieldname):
	# see if this is a Many-to-many field. If yes, we want to print
	# it out as a pretty list
	if isinstance(obj._meta.get_field_by_name(fieldname)[0], models.ManyToManyField):
		# NOTE! If the object is brand new, and it has a many-to-many relationship, we can't
		# access this data yet. So just return that it's not available yet.
		if not obj.pk:
			# No primary key indicates the object doesn't exist yet, so we can't
			# access the primary key
			return "<not available yet>"
		return u", ".join(map(lambda x: unicode(x), getattr(obj, fieldname).all()))
	return getattr(obj, fieldname)

def _get_full_text_representation(obj):
	fieldlist = _get_all_notification_fields(obj)
	if not fieldlist:
		return "This object does not know how to express itself."

	return "\n".join([u'%s: %s' % (n, _get_attr_value(obj, n)) for n in fieldlist])

def _get_notification_text(obj):
	try:
		oldobj = obj.__class__.objects.get(pk=obj.pk)
	except obj.DoesNotExist:
		return ('A new {0} as been added'.format(obj._meta.verbose_name),
				_get_full_text_representation(obj))

	if hasattr(obj, 'approved'):
			# This object has the capability to do approving. Apply the following logic:
			# 1. If object was unapproved, and is still unapproved, don't send notification
			# 2. If object was unapproved, and is now approved, send "object approved" notification
			# 3. If object was approved, and is no longer approved, send "object unapproved" notification
			# 4. (FIXME: configurable?) If object was approved and is still approved, send changes notification
		if not obj.approved:
			if not oldobj.approved:
				# Was approved, still approved -> no notification
				return (None, None)
			# From approved to unapproved
			return ('{0} id {1} has been unapproved'.format(obj._meta.verbose_name, obj.id),
					_get_full_text_representation(obj))
		else:
			if not oldobj.approved:
				# Object went from unapproved to approved
				return ('{0} id {1} has been approved'.format(obj._meta.verbose_name, obj.id),
						_get_full_text_representation(obj))
			# Object contents have changed. Generate a diff!
		diff = _get_full_text_diff(obj, oldobj)
		if not diff:
			return (None, None)
		return ('{0} id {1} has been modified'.format(obj._meta.verbose_name, obj.id),
				'The following fields have been modified:\n\n%s' % diff)
	else:
		# If there is no approved field, but send_notifications was set
		# to True, we notify on all changes.
		diff = _get_full_text_diff(obj, oldobj)
		if not diff:
			return (None, None)
		return ('{0} id {1} has been modified'.format(obj._meta.verbose_name, obj.id),
				'The following fields have been modified:\n\n%s' % diff)

def my_pre_save_handler(sender, **kwargs):
	instance = kwargs['instance']
	if getattr(instance, 'send_notification', False):
		(subj, cont) = _get_notification_text(instance)
		if cont:
			cont = _build_url(instance) + "\n\n" + cont
			send_simple_mail(settings.NOTIFICATION_FROM,
							 settings.NOTIFICATION_EMAIL,
							 "%s by %s" % (subj, get_current_user()),
							 cont)

def my_pre_delete_handler(sender, **kwargs):
	instance = kwargs['instance']
	if getattr(instance, 'send_notification', False):
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
		map(varnish_purge, purgelist)

def register_basic_signal_handlers():
	pre_save.connect(my_pre_save_handler)
	pre_delete.connect(my_pre_delete_handler)
	post_save.connect(my_post_save_handler)
