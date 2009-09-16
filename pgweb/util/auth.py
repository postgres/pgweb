from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.db import connection

# Special version of the authentication backend, so we can deal with migration
# of accounts from the old community login system. Once we consider all accounts
# migrated, we can remove this one and use the default backend.
class AuthBackend(ModelBackend):
	def authenticate(self, username=None, password=None):
		try:
			user = User.objects.get(username=username)

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
			curs.execute('SELECT * FROM community_login_old(%s,%s)', (username, password))
			rows = curs.fetchall()
			if len(rows) != 1:
				# No rows returned, something clearly went wrong
				return None
			if rows[0][1] == 1:
				# Value 1 in field 1 means the login succeeded. In this case,
				# create a user in the django system, and migrate all settings
				# we can think of.
				user = User(username=username, password=password, email=rows[0][3], first_name=rows[0][2])
				user.save()
				return user
			# Any other value in field 1 means login failed, so tell django we did
			return None

		return None # Should never get here, but just in case...

