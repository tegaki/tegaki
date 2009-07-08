# Sample Django settings for tegakidb project.
# Copy your own to ../../tegakidb/ and edit it with your personal settings.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2' # 'postgresql_psycopg2', 'postgresql',
                                        # 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'tegakidb' # Or path to database file if using sqlite3
DATABASE_USER = 'tegaki' # Not used with sqlite3
DATABASE_PASSWORD = '' # Not used with sqlite3
DATABASE_HOST = 'localhost' # Set to empty string for localhost. 
                            # Not used with sqlite3.
DATABASE_PORT = ''   # Set to empty string for localhost. 
                     # Not used with sqlite3.       

import os
TEGAKIDB_ROOT = '/path/to/hwr/tegaki-db'
WEBCANVAS_ROOT = '/path/to/hwr/tegaki-webcanvas/webcanvas'

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(TEGAKIDB_ROOT, 'data/www/')

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
# This should of course point to the actual domain using to host (see usage
# guide for setting up apache)
MEDIA_URL = 'http://localhost/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'secret-key'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
)


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'dojango.middleware.DojoAutoRequireMiddleware',
)

AUTH_PROFILE_MODULE = 'users.TegakiUser'

DOJANGO_DATAGRID_ACCESS = (
    'users.TegakiUser',
    'hwdb.HandwritingSample',
)

LOGIN_URL = '/tegaki/login/'
LOGIN_REDIRECT_URL = '/tegaki/'

ROOT_URLCONF = 'tegakidb.urls'

TEMPLATE_DIRS = (
    TEGAKIDB_ROOT + '/data/templates/',
)

TEMPLATE_DIRS = (
    os.path.join(TEGAKIDB_ROOT, 'data/templates/'),
)

FIXTURE_DIRS = (
    os.path.join(TEGAKIDB_ROOT, 'data/fixtures/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',

    'tegakidb.dojango',
                
    'tegakidb.hwdb',    
    'tegakidb.news',
    'tegakidb.users'
)
