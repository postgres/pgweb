from email.mime.text import MIMEText

from django.db.models.signals import pre_save, post_save
from django.db import models
from django.conf import settings

from util.middleware import get_current_user
from util.misc import sendmail, varnish_purge

class PgModel(object):
	send_notification = False
	purge_urls = ()
	notify_fields = None
	modifying_user = None

	def PostSaveHandler(self):
		"""
		If a set of URLs are available as purge_urls, then send commands
		to the cache to purge those urls.
		"""
		if callable(self.purge_urls):
			purgelist = self.purge_urls()
		else:
			if not self.purge_urls: return
			purgelist = self.purge_urls
		map(varnish_purge, purgelist)


	def PreSaveHandler(self):
		"""If send_notification is set to True, send a default formatted notification mail"""
		
		if not self.send_notification:
			return

		(subj, cont) = self._get_changes_texts()
		
		if not cont:
			# If any of these come back as None, it means that nothing actually changed,
			# or that we don't care to send out notifications about it.
			return

		cont = self._build_url() + "\n\n" + cont


		# Build the mail text
		msg = MIMEText(cont, _charset='utf-8')
		msg['Subject'] = "%s by %s" % (subj, get_current_user())
		msg['To'] = settings.NOTIFICATION_EMAIL
		msg['From'] = settings.NOTIFICATION_FROM

		if hasattr(settings,'SUPPRESS_NOTIFICATIONS') and settings.SUPPRESS_NOTIFICATIONS:
			print msg.as_string()
		else:
			sendmail(msg)

	def delete(self):
		# We can't compare the object, but we should be able to construct something anyway
		if self.send_notification:
			subject = "%s id %s has been deleted by %s" % (
				self._meta.verbose_name,
				self.id,
				get_current_user())
			msg = MIMEText(self.full_text_representation(), _charset='utf-8')
			msg['Subject'] = subject
			msg['To'] = settings.NOTIFICATION_EMAIL
			msg['From'] = settings.NOTIFICATION_FROM
			if hasattr(settings,'SUPPRESS_NOTIFICATIONS') and settings.SUPPRESS_NOTIFICATIONS:
				print msg.as_string()
			else:
				sendmail(msg)

		# Now call our super to actually delete the object
		super(PgModel, self).delete()
		
	def _get_changes_texts(self):
		try:
			oldobj = self.__class__.objects.get(pk=self.pk)
		except self.DoesNotExist, e:
			return ('A new %s has been added' % self._meta.verbose_name, self.full_text_representation())
		if hasattr(self,'approved'):
			# This object has the capability to do approving. Apply the following logic:
			# 1. If object was unapproved, and is still unapproved, don't send notification
			# 2. If object was unapproved, and is now approved, send "object approved" notification
			# 3. If object was approved, and is no longer approved, send "object unapproved" notification
			# 4. (FIXME: configurable?) If object was approved and is still approved, send changes notification
			if not self.approved:
				if not oldobj.approved:
					# Still unapproved, just accept the changes
					return (None, None)
				# Went from approved to unapproved
				return ('%s id %s has been unapproved' % (self._meta.verbose_name, self.id), self.full_text_representation())
			else:
				if not oldobj.approved:
					# Object went from unapproved to approved
					return ('%s id %s has been approved' % (self._meta.verbose_name, self.id),
						self.full_text_representation())
				# Object contents have changed. Generate a diff!
				diff = self.full_text_diff(oldobj)
				if not diff:
					return (None, None)
				return ('%s id %s has been modified' % (self._meta.verbose_name, self.id),
					"The following fields have been modified:\n\n%s" % diff)
		else:
			# If there is no approved field, but send_notifications was set
			# to True, we notify on all changes.
			diff = self.full_text_diff(oldobj)
			if not diff:
				return (None, None)
			return ('%s id %s has been modified' % (self._meta.verbose_name, self.id),
					"The following fields have been modified:\n\n%s" % diff)

	def _get_all_notification_fields(self):
		if self.notify_fields:
			return self.notify_fields
		else:
			# Include all field names except specified ones, that are "direct" (by get_field_by_name()[2])
			return [n for n in self._meta.get_all_field_names() if not n in ('approved', 'submitter', 'id', ) and self._meta.get_field_by_name(n)[2]]
	
	def full_text_representation(self):
		fieldlist = self._get_all_notification_fields()
		if not fieldlist:
			return "This object does not know how to express itself."

		return "\n".join(['%s: %s' % (n, self._get_attr_value(n)) for n in fieldlist])

	def _get_attr_value(self, fieldname):
		try:
			# see if this is a Many-to-many field, if yes, we want to print out a pretty list
			value = getattr(self, fieldname)
			if isinstance(self._meta.get_field_by_name(fieldname)[0], models.ManyToManyField):
				return ", ".join(map(lambda x: unicode(x), value.all()))
			return value
		except ValueError, v:
			# NOTE! If the object is brand new, and it has a many-to-many relationship, we can't
			# access this data yet. So just return that it's not available yet.
			# XXX: This is an ugly way to find it out, and is dependent on
			#      the version of django used. But I've found no better way...
			if v.message.find('" needs to have a value for field "') and v.message.find('" before this many-to-many relationship can be used.') > -1:
				return "<not available yet>"
			else:
				raise v

	def _build_url(self):
		if self.id:
			return "%s/admin/%s/%s/%s/" % (
				settings.SITE_ROOT,
				self._meta.app_label,
				self._meta.module_name,
				self.id,
			)
		else:
			return "%s/admin/%s/%s/" % (
				settings.SITE_ROOT,
				self._meta.app_label,
				self._meta.module_name,
			)

	def full_text_diff(self, oldobj):
		fieldlist = self._get_all_notification_fields()
		if not fieldlist:
			return "This object does not know how to express ifself."
		
		s = "\n\n".join(["%s from: %s\n%s to:   %s" % (
			n,
			oldobj._get_attr_value(n),
			n,
			self._get_attr_value(n),
		) for n in fieldlist if oldobj._get_attr_value(n) != self._get_attr_value(n)])
		if not s: return None
		return s


def my_pre_save_handler(sender, **kwargs):
	instance = kwargs['instance']
	if isinstance(instance, PgModel):
		instance.PreSaveHandler()

def my_post_save_handler(sender, **kwargs):
	instance = kwargs['instance']
	if isinstance(instance, PgModel):
		instance.PostSaveHandler()

def register_basic_signal_handlers():
	pre_save.connect(my_pre_save_handler)
	post_save.connect(my_post_save_handler)
