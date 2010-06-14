Authentication
==============
The authentication system provides the base for the community login
system, as well as the django system. The functions defined in
sql/community_login.sql implement the community login system (existing
API) on top of the django authentication, as well as a function to
access all users defined in the old community login system.

The custom authentication provider pgweb.util.auth.AuthBackend
implements the community login system migration functionality. It will
first attempt to log the user in with the standard django system. If
this fails, it will attempt to log the user in with the *old*
community login system, and if this succeeds the user will
automatically be migrated to the django authentication system, and
removed from the old system.

In a local installation that does not have access to the existing set
of users, this authentication backend can be disabled completely, and
the system will function perfectly fine relying on just the django
authentication system.
