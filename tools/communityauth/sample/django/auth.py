#
# Django module to support postgresql.org community authentication 2.0
#
# The main location for this module is the pgweb git repository hosted
# on git.postgresql.org - look there for updates.
#
# To integrate with django, you need the following:
# * Make sure the view "login" from this module is used for login
# * Map an url somwehere (typically /auth_receive/) to the auth_receive
#   view.
# * In settings.py, set AUTHENTICATION_BACKENDS to point to the class
#   AuthBackend in this module.
# * (And of course, register for a crypto key with the main authentication
#   provider website)
# * If the application uses the django admin interface, the login screen
#   has to be replaced with something similar to login.html in this
#   directory (adjust urls, and name it admin/login.html in any template
#   directory that's processed before the default django.contrib.admin)
#

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.conf import settings

import base64
import json
import socket
from urllib.parse import urlparse, urlencode, parse_qs
import requests
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHA
from Cryptodome import Random
import time


class AuthBackend(ModelBackend):
    # We declare a fake backend that always fails direct authentication -
    # since we should never be using direct authentication in the first place!
    def authenticate(self, username=None, password=None):
        raise Exception("Direct authentication not supported")


####
# Two regular django views to interact with the login system
####

# Handle login requests by sending them off to the main site
def login(request):
    if 'next' in request.GET:
        # Put together an url-encoded dict of parameters we're getting back,
        # including a small nonce at the beginning to make sure it doesn't
        # encrypt the same way every time.
        s = "t=%s&%s" % (int(time.time()), urlencode({'r': request.GET['next']}))
        # Now encrypt it
        r = Random.new()
        iv = r.read(16)
        encryptor = AES.new(SHA.new(settings.SECRET_KEY.encode('ascii')).digest()[:16], AES.MODE_CBC, iv)
        cipher = encryptor.encrypt(s.encode('ascii') + b' ' * (16 - (len(s) % 16)))  # pad to 16 bytes

        return HttpResponseRedirect("%s?d=%s$%s" % (
            settings.PGAUTH_REDIRECT,
            base64.b64encode(iv, b"-_").decode('utf8'),
            base64.b64encode(cipher, b"-_").decode('utf8'),
        ))
    else:
        return HttpResponseRedirect(settings.PGAUTH_REDIRECT)


# Handle logout requests by logging out of this site and then
# redirecting to log out from the main site as well.
def logout(request):
    if request.user.is_authenticated:
        django_logout(request)
    return HttpResponseRedirect("%slogout/" % settings.PGAUTH_REDIRECT)


# Receive an authentication response from the main website and try
# to log the user in.
def auth_receive(request):
    if 's' in request.GET and request.GET['s'] == "logout":
        # This was a logout request
        return HttpResponseRedirect('/')

    if 'i' not in request.GET:
        return HttpResponse("Missing IV in url!", status=400)
    if 'd' not in request.GET:
        return HttpResponse("Missing data in url!", status=400)

    # Set up an AES object and decrypt the data we received
    decryptor = AES.new(base64.b64decode(settings.PGAUTH_KEY),
                        AES.MODE_CBC,
                        base64.b64decode(str(request.GET['i']), "-_"))
    s = decryptor.decrypt(base64.b64decode(str(request.GET['d']), "-_")).rstrip(b' ').decode('utf8')

    # Now un-urlencode it
    try:
        data = parse_qs(s, strict_parsing=True)
    except ValueError:
        return HttpResponse("Invalid encrypted data received.", status=400)

    # Check the timestamp in the authentication
    if (int(data['t'][0]) < time.time() - 10):
        return HttpResponse("Authentication token too old.", status=400)

    # Update the user record (if any)
    try:
        user = User.objects.get(username=data['u'][0])
        # User found, let's see if any important fields have changed
        changed = False
        if user.first_name != data['f'][0]:
            user.first_name = data['f'][0]
            changed = True
        if user.last_name != data['l'][0]:
            user.last_name = data['l'][0]
            changed = True
        if user.email != data['e'][0]:
            user.email = data['e'][0]
            changed = True
        if changed:
            user.save()
    except User.DoesNotExist:
        # User not found, create it!

        # NOTE! We have some legacy users where there is a user in
        # the database with a different userid. Instead of trying to
        # somehow fix that live, give a proper error message and
        # have somebody look at it manually.
        if User.objects.filter(email=data['e'][0]).exists():
            return HttpResponse("""A user with email %s already exists, but with
a different username than %s.

This is almost certainly caused by some legacy data in our database.
Please send an email to webmaster@postgresql.org, indicating the username
and email address from above, and we'll manually merge the two accounts
for you.

We apologize for the inconvenience.
""" % (data['e'][0], data['u'][0]), content_type='text/plain')

        if getattr(settings, 'PGAUTH_CREATEUSER_CALLBACK', None):
            res = getattr(settings, 'PGAUTH_CREATEUSER_CALLBACK')(
                data['u'][0],
                data['e'][0],
                ['f'][0],
                data['l'][0],
            )
            # If anything is returned, we'll return that as our result.
            # If None is returned, it means go ahead and create the user.
            if res:
                return res

        user = User(username=data['u'][0],
                    first_name=data['f'][0],
                    last_name=data['l'][0],
                    email=data['e'][0],
                    password='setbypluginnotasha1',
                    )
        user.save()

    # Ok, we have a proper user record. Now tell django that
    # we're authenticated so it persists it in the session. Before
    # we do that, we have to annotate it with the backend information.
    user.backend = "%s.%s" % (AuthBackend.__module__, AuthBackend.__name__)
    django_login(request, user)

    # Finally, check of we have a data package that tells us where to
    # redirect the user.
    if 'd' in data:
        (ivs, datas) = data['d'][0].split('$')
        decryptor = AES.new(SHA.new(settings.SECRET_KEY.encode('ascii')).digest()[:16],
                            AES.MODE_CBC,
                            base64.b64decode(ivs, b"-_"))
        s = decryptor.decrypt(base64.b64decode(datas, "-_")).rstrip(b' ').decode('utf8')
        try:
            rdata = parse_qs(s, strict_parsing=True)
        except ValueError:
            return HttpResponse("Invalid encrypted data received.", status=400)
        if 'r' in rdata:
            # Redirect address
            return HttpResponseRedirect(rdata['r'][0])
    # No redirect specified, see if we have it in our settings
    if hasattr(settings, 'PGAUTH_REDIRECT_SUCCESS'):
        return HttpResponseRedirect(settings.PGAUTH_REDIRECT_SUCCESS)
    return HttpResponse("Authentication successful, but don't know where to redirect!", status=500)


# Perform a search in the central system. Note that the results are returned as an
# array of dicts, and *not* as User objects. To be able to for example reference the
# user through a ForeignKey, a User object must be materialized locally. We don't do
# that here, as this search might potentially return a lot of unrelated users since
# it's a wildcard match.
# Unlike the authentication, searching does not involve the browser - we just make
# a direct http call.
def user_search(searchterm=None, userid=None):
    # If upstream isn't responding quickly, it's not going to respond at all, and
    # 10 seconds is already quite long.
    socket.setdefaulttimeout(10)
    if userid:
        q = {'u': userid}
    else:
        q = {'s': searchterm}

    r = requests.get(
        '{0}search/'.format(settings.PGAUTH_REDIRECT),
        params=q,
    )
    if r.status_code != 200:
        return []

    (ivs, datas) = r.text.encode('utf8').split(b'&')

    # Decryption time
    decryptor = AES.new(base64.b64decode(settings.PGAUTH_KEY),
                        AES.MODE_CBC,
                        base64.b64decode(ivs, "-_"))
    s = decryptor.decrypt(base64.b64decode(datas, "-_")).rstrip(b' ').decode('utf8')
    j = json.loads(s)

    return j


# Import a user into the local authentication system. Will initially
# make a search for it, and if anything other than one entry is returned
# the import will fail.
# Import is only supported based on userid - so a search should normally
# be done first. This will result in multiple calls to the upstream
# server, but they are cheap...
# The call to this function should normally be wrapped in a transaction,
# and this function itself will make no attempt to do anything about that.
def user_import(uid):
    u = user_search(userid=uid)
    if len(u) != 1:
        raise Exception("Internal error, duplicate or no user found")

    u = u[0]

    if User.objects.filter(username=u['u']).exists():
        raise Exception("User already exists")

    User(username=u['u'],
         first_name=u['f'],
         last_name=u['l'],
         email=u['e'],
         password='setbypluginnotsha1',
         ).save()
