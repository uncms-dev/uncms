"""
Production settings for {{ project_name }} project.

For an explanation of these settings, please see the Django documentation at:

<http://docs.djangoproject.com/en/dev/>

While many of these settings assume sensible defaults, you must provide values
for the site, database, media and email sections below.
"""

from social.pipeline import DEFAULT_AUTH_PIPELINE

import os


# The name of this site.  Used for branding in the online admin area.

SITE_NAME = "Example"

SITE_DOMAIN = "example.com"

PREPEND_WWW = True

ALLOWED_HOSTS = [
    SITE_DOMAIN,
    'www.{}'.format(SITE_DOMAIN)
]

SUIT_CONFIG = {
    'ADMIN_NAME': SITE_NAME
}

# Database settings.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "{{ project_name }}",
        "USER": "{{ project_name }}",
        "PASSWORD": "",
        "HOST": "",
        "PORT": ""
    }
}


# Absolute path to the directory where all uploaded media files are stored.

MEDIA_ROOT = "/var/www/{{ project_name }}_media"

MEDIA_URL = "/media/"

FILE_UPLOAD_PERMISSIONS = 0o644


# Absolute path to the directory where static files will be collected.

STATIC_ROOT = "/var/www/{{ project_name }}_static"

STATIC_URL = "/static/"


# Email settings.

EMAIL_HOST = ""

EMAIL_HOST_USER = "{{ project_name }}"

EMAIL_HOST_PASSWORD = ""

EMAIL_PORT = 587

EMAIL_USE_TLS = True

SERVER_EMAIL = u"{name} <notifications@{domain}>".format(
    name=SITE_NAME,
    domain=SITE_DOMAIN,
)

DEFAULT_FROM_EMAIL = SERVER_EMAIL

EMAIL_SUBJECT_PREFIX = "[%s] " % SITE_NAME


# Error reporting settings.  Use these to set up automatic error notifications.

ADMINS = (
    ("Onespacemedia Errors", "errors@onespacemedia.com"),
)

MANAGERS = ()

SEND_BROKEN_LINK_EMAILS = False


# Locale settings.

TIME_ZONE = "Europe/London"

LANGUAGE_CODE = "en-gb"

USE_I18N = False

USE_L10N = True

USE_TZ = True


# Auto-discovery of project location.

SITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# A list of additional installed applications.

INSTALLED_APPS = (

    "django.contrib.sessions",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "suit",
    "django.contrib.admin",
    "django.contrib.sitemaps",

    "sorl.thumbnail",
    "compressor",

    "cms",

    "reversion",
    "usertools",
    "historylinks",
    "watson",

    "cms.apps.pages",
    "cms.apps.links",
    "cms.apps.media",
    "cms.apps.news",

    "{{ project_name }}.apps.site",
    "{{ project_name }}.apps.faqs",
    "{{ project_name }}.apps.jobs",
    "{{ project_name }}.apps.people",

    'server_management',
    'django_extensions',

    'social.apps.django_app.default',
)


# Additional static file locations.

STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, "static"),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# Dispatch settings.

MIDDLEWARE_CLASSES = (
    "django.middleware.transaction.TransactionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "watson.middleware.SearchContextMiddleware",
    "historylinks.middleware.HistoryLinkFallbackMiddleware",
    "cms.middleware.PublicationMiddleware",
    "cms.apps.pages.middleware.PageMiddleware",
)

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)


ROOT_URLCONF = "{{ project_name }}.urls"

WSGI_APPLICATION = "{{ project_name }}.wsgi.application"

PUBLICATION_MIDDLEWARE_EXCLUDE_URLS = (
    "^admin/.*",
)

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

SITE_ID = 1

# Absolute path to the directory where templates are stored.

TEMPLATE_DIRS = (
    os.path.join(SITE_ROOT, "templates"),
)

TEMPLATE_LOADERS = (
    ("django.template.loaders.cached.Loader", (
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    )),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "cms.context_processors.settings",
    "cms.apps.pages.context_processors.pages",
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
)


# Namespace for cache keys, if using a process-shared cache.

CACHE_MIDDLEWARE_KEY_PREFIX = "{{ project_name }}"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}


# A secret key used for cryptographic algorithms.

SECRET_KEY = "{{ secret_key }}"


REDACTOR_OPTIONS = {
    "plugins": ["table", "imagemanager", "video", "filemanager"],
    "imageUpload": "/admin/media/file/redactor/upload/image/",
    "fileUpload": "/admin/media/file/redactor/upload/file/",
    "minHeight": 300,
    "formattingAdd": [
        {
            "tag": "a",
            "title": "Button",
            "class": "button primary",
        }
    ]
}


NEWS_APPROVAL_SYSTEM = False

GOOGLE_ANALYTICS = ''

# You can get your Client ID & Secret here: https://creativesdk.adobe.com/myapps.html
ADOBE_CREATIVE_SDK_ENABLED = False
ADOBE_CREATIVE_SDK_CLIENT_SECRET = ''
ADOBE_CREATIVE_SDK_CLIENT_ID = ''

# Google Apps authentication.

# SETUP:
# 1. https://console.developers.google.com/project
# 2. "Create project"
# 3. APIs & auth -> Consent screen
# 4. Select email address
# 5. APIs & auth -> APIs
# 6. Enable "Google+ API"
# 7. APIs & auth -> Credentials
# 8. Create new Client ID -> Web application
# 9. Copy Client ID to KEY below.
# 10. Copy Client Secret to SECRET below.
# 11. Edit settings
# 12. Set authorized domain

AUTHENTICATION_BACKENDS = (
    'social.backends.google.GooglePlusAuth',
    'django.contrib.auth.backends.ModelBackend'
)

SOCIAL_AUTH_GOOGLE_PLUS_KEY = ''
SOCIAL_AUTH_GOOGLE_PLUS_SECRET = ''
WHITELISTED_DOMAINS = ['onespacemedia.com']

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/admin/'
SOCIAL_AUTH_PIPELINE = DEFAULT_AUTH_PIPELINE + (
    'cms.pipeline.make_staff',
)
