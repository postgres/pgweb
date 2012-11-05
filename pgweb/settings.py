# Django settings for pgweb project.

DEBUG = False
#TEMPLATE_DEBUG = DEBUG

ADMINS = (
	('PostgreSQL Webmaster', 'webmaster@postgresql.org'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

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

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/adminmedia/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'REALLYCHANGETHISINSETTINGS_LOCAL.PY'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'util.middleware.PgMiddleware',
]

ROOT_URLCONF = 'pgweb.urls'

TEMPLATE_DIRS = (
    '../templates/',
	'../../templates', # Sometimes called in subdirectories, should never hurt to have both
)

TEMPLATE_CONTEXT_PROCESSORS = (
	'django.core.context_processors.auth',
	'django.core.context_processors.media',
	'util.contexts.RootLinkContextProcessor',
)

LOGIN_URL='/account/login/'
LOGIN_REDIRECT_URL='/account/'
LOGOUT_URL='/account/logout/'

AUTHENTICATION_BACKENDS = (
    'util.auth.AuthBackend',
)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.markup',
    'pgweb.core',
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
	'pgweb.pwn',
	'pgweb.search',
]


###
# Application specific settings, likely overridden in settings_local.py.
#
# In particular, adjust the email addresses
###
SESSION_COOKIE_SECURE=True                             # Allow our session only over https
SESSION_COOKIE_DOMAIN="www.postgresql.org"             # Don't allow access by other postgresql.org sites
SITE_ROOT="http://www.postgresql.org"                  # Root of working URLs
FTP_PICKLE="/usr/local/pgweb/ftpsite.pickle"           # Location of file with current contents from ftp site
NOTIFICATION_EMAIL="someone@example.com"               # Address to send notifications *to*
NOTIFICATION_FROM="someone@example.com"                # Address to send notifications *from*
LISTSERVER_EMAIL="someone@example.com"                 # Address to majordomo
BUGREPORT_EMAIL="someone@example.com"                  # Address to pgsql-bugs list
SUPPRESS_NOTIFICATIONS=False                           # Set to true to disable all notification mails
NO_HTTPS_REDIRECT=False                                # Set to true to disable redirects to https when
                                                       # developing locally
FRONTEND_SERVERS=()                                    # A tuple containing the *IP addresses* of all the
                                                       # varnish frontend servers in use.
FTP_MASTERS=()										   # A tuple containing the *IP addresses* of all machines
                                                       # trusted to upload ftp structure data
VARNISH_PURGERS=()                                     # Extra servers that can do varnish purges through our queue

# Load local settings overrides
from settings_local import *

