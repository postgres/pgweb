# Django settings for pgweb project.

DEBUG = False
#TEMPLATE_DEBUG = DEBUG

ADMINS = (
	('PostgreSQL Webmaster', 'webmaster@postgresql.org'),
)

MANAGERS = ADMINS

DATABASES={
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2',
		'NAME': 'pgweb',
		}
	}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'GMT'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''
STATIC_URL = '/media/'

STATICFILES_DIRS = (
	'media/',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'REALLYCHANGETHISINSETTINGS_LOCAL.PY'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'pgweb.util.middleware.PgMiddleware',
]

CSRF_FAILURE_VIEW='pgweb.core.views.csrf_failure'

ROOT_URLCONF = 'pgweb.urls'

TEMPLATE_DIRS = (
    'templates/',
	'../templates', # Sometimes called in subdirectories, should never hurt to have both
)

TEMPLATE_CONTEXT_PROCESSORS = (
	'django.contrib.auth.context_processors.auth',
	'django.contrib.messages.context_processors.messages',
	'django.core.context_processors.media',
	'pgweb.util.contexts.PGWebContextProcessor',
)

LOGIN_URL='/account/login/'
LOGIN_REDIRECT_URL='/account/'
LOGOUT_URL='/account/logout/'

AUTHENTICATION_BACKENDS = (
    'pgweb.util.auth.AuthBackend',
)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django_markwhat',
	'django.contrib.staticfiles',
    'pgweb.selectable',
    'pgweb.core',
    'pgweb.mailqueue',
    'pgweb.account',
    'pgweb.news',
    'pgweb.events',
    'pgweb.quotes',
    'pgweb.downloads',
    'pgweb.docs',
    'pgweb.contributors',
    'pgweb.profserv',
    'pgweb.lists',
    'pgweb.sponsors',
    'pgweb.survey',
    'pgweb.misc',
    'pgweb.featurematrix',
	'pgweb.search',
    'pgweb.pugs',
]

#
# Disable the new authentication handling for now. The reason for this is
# that we need the sha1 authentication so we can do old-style community
# auth, which is still used by the commitfest app. Once that app is
# migrated away, this can be reverted to the new django default which
# is more secure.
#
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

# Default format for date/time (as it changes between machines)
DATETIME_FORMAT="Y-m-d H:i:s"

# Configure recaptcha. Most details contain keys and are thus handled
# in settings_local.py. Override NOCAPTCHA to actually use them.
NOCAPTCHA=True
RECAPTCHA_SITE_KEY=""
RECAPTCHA_SECRET_KEY=""

###
# Application specific settings, likely overridden in settings_local.py.
#
# In particular, adjust the email addresses
###
SESSION_COOKIE_SECURE=True                             # Allow our session only over https
SESSION_COOKIE_DOMAIN="www.postgresql.org"             # Don't allow access by other postgresql.org sites
SESSION_COOKIE_HTTPONLY=True                           # Access over http only, no js
CSRF_COOKIE_SECURE=SESSION_COOKIE_SECURE
CSRF_COOKIE_DOMAIN=SESSION_COOKIE_DOMAIN
CSRF_COOKIE_HTTPONLY=SESSION_COOKIE_HTTPONLY

SITE_ROOT="http://www.postgresql.org"                  # Root of working URLs
FTP_PICKLE="/usr/local/pgweb/ftpsite.pickle"           # Location of file with current contents from ftp site
STATIC_CHECKOUT="/usr/local/pgweb-static"              # Location of a checked out pgweb-static project
NOTIFICATION_EMAIL="someone@example.com"               # Address to send notifications *to*
NOTIFICATION_FROM="someone@example.com"                # Address to send notifications *from*
LISTSERVER_EMAIL="someone@example.com"                 # Address to majordomo
BUGREPORT_EMAIL="someone@example.com"                  # Address to pgsql-bugs list
DOCSREPORT_EMAIL="someone@example.com"                 # Address to pgsql-docs list
FRONTEND_SERVERS=()                                    # A tuple containing the *IP addresses* of all the
                                                       # varnish frontend servers in use.
FTP_MASTERS=()										   # A tuple containing the *IP addresses* of all machines
                                                       # trusted to upload ftp structure data
VARNISH_PURGERS=()                                     # Extra servers that can do varnish purges through our queue
ARCHIVES_SEARCH_SERVER="archives.postgresql.org"       # Where to post REST request for archives search
FRONTEND_SMTP_RELAY="magus.postgresql.org"             # Where to relay user generated email
SITE_UPDATE_TRIGGER_FILE='/tmp/pgweb.update_trigger'   # Where to drop update trigger file
SITE_UPDATE_HOSTS=('127.0.0.1', )                      # Hosts that can trigger a site update

# Load local settings overrides
from settings_local import *

