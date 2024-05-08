Development install
===================

So, you're ready to contribute to pgweb, and you want to set up a
local working copy of the website code, so you have something to work
with. Here's a quick step-by-step on how to do that:

#. Make sure you have downloaded and installed django *version 4.2*,
   and python 3 (tested with version 3.9).

   You will also need a few other dependencies, see the
   `requirements.txt` in the root directory.

   It is recommended to make the installation using a `virtualenv`

#. Make sure you have downloaded and installed PostgreSQL (tested
   with version 11, but should work fine with anything newer)

#. Create a database in your PostgreSQL installation called pgweb
   (other names are of course possible, but that's the standard one)

#. Create a file called settings_local.py, located in the pgweb
   directory (next to settings.py). This file will contain any settings
   you override from the main settings one. Normally, you will want to
   override the following::

	DEBUG=True
	SITE_ROOT="http://localhost:8000"
	SESSION_COOKIE_SECURE=False
	SESSION_COOKIE_DOMAIN=None
	CSRF_COOKIE_SECURE=False
	CSRF_COOKIE_DOMAIN=None

   There are some parts of the site that require further settings, but
   this should be enough to get the basics up and running.

#. In the pgweb directory run the following command to create all
   tables and indexes, as well as create a superuser for your local
   installation::

       ./manage.py migrate

#. A few functions are required, or at least recommended in order to
   test all of the system. The SQL scripts in the directory sql/ needs
   to be run in the database. Note that for a local dev install
   without varnish frontends, you should use the *varnish_local.sql*
   script, and not use the *varnish.sql* script.

   Load these files with something like::

       psql -d pgweb -f sql/varnish_local.sql

#. To load some initial data for some tables (far from all at this
   point), in the pgweb directory, run the following command::

       pgweb/load_initial_data.sh

#. You'll want to creaet a superuser so you can access the `/admin/`
   interface::

       ./manage.py createsuperuser

#. At this point, you're ready to get started. Start your local server
   by running::

       ./manage.py runserver

#. Now load up the website by going to http://localhost:8000

Future improvements
-------------------
The plan is to make it possible to get a good snapshot of the actual
PostgreSQL website to do development work on, including parts from the
database. However, there are a number of privacy issues that need to
be figured out before we can do that (we don't want to put a
database-dump containing thousands of well confirmed email addresses
easily available for download, for example). Any suggestions on
exactly how to get this done are much appreciated.
