from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.db import connection

# Special version of the authentication backend, so we can deal with migration
# of accounts from the old community login system. Once we consider all accounts
# migrated, we can remove this one and use the default backend.
class AuthBackend(ModelBackend):
	def authenticate(self, username=None, password=None):
		try:
			user = User.objects.get(username=username.lower())

			# If user is found, check the password using the django
			# methods alone.
			if user.check_password(password):
				return user

			# User found but password wrong --> tell django it is wrong
			return None
		except User.DoesNotExist:
			# User does not exist. See if it exists in the old system,
			# and if it does, migrate it to the new one.
			curs = connection.cursor()
			curs.execute('SELECT * FROM community_login_old(%s,%s)', (username.lower(), password))
			rows = curs.fetchall()

			if len(rows) != 1:
				# No rows returned, something clearly went wrong
				return None
			if rows[0][1] == 1:
				# Value 1 in field 1 means the login succeeded. In this case,
				# create a user in the django system, and migrate all settings
				# we can think of.
				namepieces = rows[0][2].split(None, 2)
				if len(namepieces) == 1: namepieces[1] = ''
				user = User(username=username.lower(), email=rows[0][3], first_name=namepieces[0], last_name=namepieces[1])
				user.set_password(password)
				user.save()

				# Now delete the user in the old system so nobody can use it
				curs.execute('SELECT * FROM community_login_old_delete(%s)', (username.lower(), ))

				return user
			# Any other value in field 1 means login failed, so tell django we did
			return None

		return None # Should never get here, but just in case...

