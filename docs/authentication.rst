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


Community authentication 2.0
============================
While the old community authentication system was simply having the
clients call a PostgreSQL function on the main website server, version
2.0 of the system uses browser redirects to perform this. This allows
for a number of advantages:

* The users password never hits the "community sites", only the main
  website. This has some obvious security advantages.
* There is no need to allow external access from these sites to the
  PostgreSQL database on the main website.
* It is possible for the user to get single sign-on between all the
  community sites, not just same-password.

Each community site is still registered in the central system, to hold
encryption keys and similar details. This is now held in the main
database, accessible through the django administration system, instead
of being held in pg_hba.conf and managed through SQL.

In some cases this may be complicated to implement on the client side,
and thus version 1.0 community login is still left around. It may
be removed at some point in the future, depending on implementation
and policy details...

The flow of an authentication in the 2.0 system is fairly simple:

#. The user tries to access a protected resource on the community
   site.
#. At this point, the user is redirected to an URL on the main
   website, specifically https://www.postgresql.org/account/auth/<id>/.
   The <id> number in this URL is unique for each site, and is the
   identifier that accesses all encryption keys and redirection
   information.
   In this call, the client site can optionally include a parameter
   *su*, which will be used in the final redirection step. This URL
   must start with a / to be considered, to prevent cross site
   redirection.
#. The main website will check if the user holds a valid, logged in,
   session on the main website. If it does not, the user will be
   sent through the standard login path on the main website, and once
   that is done will be sent to the next step in this process.
#. The main website puts together a dictionary of information about
   the logged in user, that contains the following fields:

   u
    The username of the user logged in
   f
     The first name of the user logged in
   l
     The last name of the user logged in
   e
     The email address of the user logged in
   su
     The suburl to redirect to (optional)
   t
     The timestamp of the authentication, in seconds-since-epoch. This
     should be validated against the current time, and authentication
     tokens older than e.g. 10 seconds should be refused.

#. This dictionary of information is then URL-encoded.
#. The resulting URL-encoded string is padded with spaces to an even
   16 bytes, and is then AES encrypted with a shared key. This key
   is stored in the main website system and indexed by the site id,
   and it is stored in the settings of the community website somewhere.
   Since this key is what protects the authentication, it should be
   treated as very valuable.
#. The resulting encrypted string and the IV used for the encryption are
   base64-encoded (in URL mode, meaning it uses - and _ instead of + and /.
#. The main website looks up the redirection URL registered for this site
   (again indexed by the site id), and constructs an URL of the format
   <redirection_url>?i=<iv>&d=<encrypted data>
#. The user browser is redirected to this URL.
#. The community website detects that this is a redirected authentication
   response, and stars processing it specifically.
#. Using the shared key, the data is decrypted (while first being base64
   decoded, of course)
#. The resulting string is urldecoded - and if any errors occur in the
   decoding, the authentication will fail. This step is guaranteed to fail
   if the encryption key is mismatching between the community site and
   the main website, since it is going to end up with something that is
   definitely not an url-decodeable string.
#. The community site will look up an existing user record under this
   username, or create a new one if one does not exist already (assuming
   the site keeps local track of users at all - if it just deals with
   session users, it can just store this information in the session).
   It is recommended that the community site verifies if the first name,
   last name or email field has changed, and updates the local record if
   this is the case.
#. The community site logs the user in using whatever method it's framework
   uses.
#. If the *su* key is present in the data structure handed over, the
   community site redirects to this location. If it's not present, then
   the community site will redirect so some default location on the
   site.
