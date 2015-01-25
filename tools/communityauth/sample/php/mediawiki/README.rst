Mediawiki login provider
------------------------

This provider implements a (fairly ugly) community auth v2 provider
for mediawiki. Since the mediawiki API doesn't support external
authentication (it requires there to be a username and password,
which isn't always true, and can only pass those on to external
services), this has to be done by browser interception. Basically,
we intercept the mediawiki login URL and redirect it. Upon receiving
the data back from the authentication system, we inject it into the
mediawiki session and redirect back. It appears to work so far...

Installation
++++++++++++
Copy all the PHP files to `/var/lib/mediawiki/pgauth/`, and
edit as necessary to have the correct URLs and keys.

Server configuration
++++++++++++++++++++
The webserver needs to be configured to intercept and redirect
the mediawiki URLs. The following configuration is required on
lighttpd::

        url.rewrite-once = (
		"^/wiki/([^?]*)(?:\?(.*))?" => "/index.php?title=$1&$2",
		"^/index.php\?title=Special:UserLogin&returnto=(.*)" => "/pgauth/login.php?r=$1",
		"^/index.php\?title=Special:UserLogout&returnto=" => "/pgauth/logout.php",
        )

It should be added after the regular mediawiki rewrites (included here
for reference on the first row).

Configuration
+++++++++++++
Edit the settings in `pgauth_conf.php` to set siteid, key and URLs. The
database connectoin string configured here is for the authentication
provider to connect to the mediawiki database, not to the community auth
database.
