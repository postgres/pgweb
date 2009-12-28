from email.mime.text import MIMEText
from subprocess import Popen, PIPE

from django.db.models.signals import pre_save
from django.db import models
from django.conf import settings

from util.middleware import get_current_user

class PgModel(object):
	send_notification = False
	notify_fields = None
	modifying_user = None

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
			pipe = Popen("sendmail -t", shell=True, stdin=PIPE).stdin
			pipe.write(msg.as_string())
			pipe.close()

		
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

		return "\n".join(['%s: %s' % (n, getattr(self, n)) for n in fieldlist])

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
			getattr(oldobj, n),
			n,
			getattr(self, n),
		) for n in fieldlist if not getattr(oldobj,n)==getattr(self,n)])
		if not s: return None
		return s


def my_pre_save_handler(sender, **kwargs):
	instance = kwargs['instance']
	if isinstance(instance, PgModel):
		instance.PreSaveHandler()

def register_basic_signal_handlers():
	pre_save.connect(my_pre_save_handler)

