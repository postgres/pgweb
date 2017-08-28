# Dump interesting information out of django sessions
#
# (This is particarly interesting when digging through old stack trace emails..)
#
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

class Command(BaseCommand):
	help = 'Dump interesting information about a session'

	def add_arguments(self, parser):
		parser.add_argument('sessionid')

	def handle(self, *args, **options):
		try:
			session = Session.objects.get(session_key=options['sessionid']).get_decoded()
			uid = session.get('_auth_user_id')
			user = User.objects.get(pk=uid)

			print u"Session {0}".format(options['sessionid'])
			print " -- Logged in user --"
			print u"Userid:   {0}".format(uid)
			print u"Username: {0}".format(user.username)
			print u"Name:     {0}".format(user.get_full_name())
			print u"Email:    {0}".format(user.email)
			# Remove known keys
			for k in ('_auth_user_id', '_auth_user_hash', '_auth_user_backend'):
				session.pop(k, None)
			if session:
				print " -- Other session values --"
				for k,v in session.items():
					print u"{0:20} {1}".format(k,v)

		except Session.DoesNotExist:
			raise CommandError('Session not found')
		except User.DoesNotExist:
			raise CommandError('Associated user not found')

