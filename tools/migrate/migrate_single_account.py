#!/usr/bin/env python
#
# This script will migrate a single user from the old system to the new one. This will
# reset the users password in the process - there is no way around that.
#
# This process is automatically done when the user logs in to the new website, but it
# is useful to do this if the user has lost his password before he/she logs into the new
# site for the first time, since the password recovery feature only works once the account
# has been migrated.
#


import sys
import os

# Set up for accessing django
from django.core.management import setup_environ
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '../../pgweb'))
import settings
setup_environ(settings)

from django.contrib.auth.models import User
from django.db import connection, transaction

from pgweb.core.models import UserProfile


from random import choice
import string

# This does not generate a strong password. But it's only a temporary one anyway,
# so this doesn't matter.
def GenPasswd(l):
	return ''.join([choice(string.letters + string.digits) for i in xrange(l)])

if __name__=="__main__":
	if len(sys.argv) != 2:
		print "Usage: migrate_single_account.py <userid>"
		sys.exit(1)

	u = sys.argv[1].lower()

	try:
		user = User.objects.get(username=u)
		print "User %s (%s %s) already exists!" % (u, user.first_name, user.last_name)
		sys.exit(1)
	except User.DoesNotExist:
		print "User does not exist in new system, that's expected..."
		pass

	transaction.enter_transaction_management()
	transaction.managed()

	# Attempt login against old system
	curs = connection.cursor()
	curs.execute("SELECT userid, fullname, email, sshkey FROM users_old WHERE userid=%s", (u,))
	rows = curs.fetchall()
	if len(rows) == 0:
		print "User %s does not exist in the old system." % u
		sys.exit(1)
	if len(rows) != 1:
		print "Userid lookup returned %s rows, not 1!" % len(rows)
		sys.exit(1)
	print "Found user %s in the old system" % u
	print "Fullname: %s" % rows[0][1]
	print "Email: %s" % rows[0][2]
	print ""
	while True:
		yn = raw_input("Are you sure you want to migrate this user, resetting his/her password? [y/n]?")
		if yn == "y":
			print "Ok, migrating..."
			break
		elif yn == "n":
			print "Aborting"
			sys.exit(1)
		else:
			continue

	pwd = GenPasswd(12)
	print "New password: %s" % pwd

	namepieces = rows[0][1].split(None, 2)
	if len(namepieces) == 0: namepieces = ['', '']
	if len(namepieces) == 1: namepieces.append('')
	print "Creating new user record..."
	user = User(username=u, email=rows[0][2], first_name=namepieces[0], last_name=namepieces[1])
	user.set_password(pwd)
	user.save()
	if rows[0][3]:
		print "Migrating SSH key..."
		profile = UserProfile(user=user)
		profile.sshkey = rows[0][3]
		profile.save()

	print "Removing user from the old system..."
	curs.execute("SELECT * FROM community_login_old_delete(%s)", (u, ))

	transaction.commit()

	print "Done. Don't forget to email the user at %s, informing him/her about the new password %s" % (rows[0][2], pwd)
