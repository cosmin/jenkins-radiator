# Django settings for jenkins_radiator project.
import os
import re

ROOT = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'radiator-cache'
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

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
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'd(lu-=w*-2w2i64u%wum9z#%_5mxm^k$(fzkx^#k-u0_)s-3na'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'jenkins_radiator.urls'

TEMPLATE_DIRS = (
    os.path.join(ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'jenkins_radiator.radiator',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
SITE_MEDIA = os.path.join(PROJECT_ROOT, "site_media")
HUDSON_URL = ''
HUDSON_BUILD_NAME_PATTERN = '_Build'
HUDSON_TEST_NAME_PATTERN = '_Test_'
HUDSON_TEST_IGNORE_REGEX = re.compile('')
HUDSON_SMOKE_NAME_REGEX = re.compile('Smoke', re.I)
HUDSON_BASELINE_NAME_REGEX = re.compile('Baseline', re.I)
HUDSON_PROJECT_NAME_REGEX = re.compile('Project', re.I)
HUDSON_BUILD_COUNT = 10
HUDSON_MAXIMUM_CONCURRENT_BUILDS = 4

# Default number of build to show in the radiator
#SWA IRC Topic config
IRC_NICK=''
#IRC_PORT=6667
#IRC_HOST=''
IRC_REALNAME=''
IRC_CHAN=''
IRC_RSP_USER=''
IRC_RSP_JOIN=''
IRC_RSP_TOPIC=''
IRC_RSP_MSG=''
IRC_TOPIC_POLL_INTERVAL_SECONDS_FLOAT=4.0
IRC_TOPIC_BUILD_NAME=''
IRC_TOPIC_ERROR_MSG=''
IRC_IDENT=''

try:
  from settings_local import *
except ImportError:
  pass


