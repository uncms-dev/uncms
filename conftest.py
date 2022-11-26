import getpass
import os

import pytest
from django.conf import settings


def pytest_configure():
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'uncms_test',
                'USER': os.environ.get('UNCMS_DB_USER', getpass.getuser()),
                'PASSWORD': os.environ.get('UNCMS_DB_PASSWORD'),
                'TEST': {
                    'NAME': 'uncms_test',
                }
            }
        },
        STATIC_URL='/static/',
        MEDIA_URL='/media/',
        MEDIA_ROOT=os.path.join(os.path.dirname(__file__), 'media/'),
        INSTALLED_APPS=[
            # Django apps
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.messages',
            'django.contrib.sessions',
            'django.contrib.sitemaps',

            # CMS apps
            'uncms',
            'uncms.apps.links',
            'uncms.apps.media',
            'uncms.apps.pages',
            'uncms.apps.testing_models',

            'uncms.plugins.moderation.tests',

            # Third party apps
            'sorl.thumbnail',
            'reversion',
            'watson',
        ],
        ROOT_URLCONF='uncms.tests.urls',
        ALLOWED_HOSTS=['*'],
        TEMPLATES=[
            {
                'BACKEND': 'django_jinja.backend.Jinja2',
                'DIRS': [
                    os.path.join('uncms', 'templates'),
                    os.path.join('uncms', 'tests', 'templates'),
                ],
                'APP_DIRS': True,
                'OPTIONS': {
                    'match_extension': '.html',
                    'match_regex': r'^(?!admin/|reversion/|registration/).*',
                    'app_dirname': 'templates',
                    'newstyle_gettext': True,
                    'bytecode_cache': {
                        'name': 'default',
                        'backend': 'django_jinja.cache.BytecodeCache',
                        'enabled': False,
                    },
                    'autoescape': True,
                    'auto_reload': False,
                    'translation_engine': 'django.utils.translation',
                    'context_processors': [
                        'django.contrib.auth.context_processors.auth',
                        'django.template.context_processors.debug',
                        'django.template.context_processors.i18n',
                        'django.template.context_processors.media',
                        'django.template.context_processors.static',
                        'django.contrib.messages.context_processors.messages',
                        'django.template.context_processors.request',
                        'uncms.apps.pages.context_processors.pages',
                    ]
                }
            },
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [
                    os.path.join('uncms', 'tests', 'templates'),
                ],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.contrib.auth.context_processors.auth',
                        'django.template.context_processors.debug',
                        'django.template.context_processors.i18n',
                        'django.template.context_processors.media',
                        'django.template.context_processors.static',
                        'django.contrib.messages.context_processors.messages',
                        'django.template.context_processors.request',
                        'uncms.apps.pages.context_processors.pages',
                    ]
                }
            }
        ],
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'uncms.apps.pages.middleware.PageMiddleware',
        ],
        SECRET_KEY='KNOWN_FIXED_VALUE_IS_FINE',
        PUBLICATION_MIDDLEWARE_EXCLUDE_URLS=['/admin/'],
        UNCMS={
            'SITE_DOMAIN': 'example.com',
        },
        THUMBNAIL_PRESERVE_FORMAT=True,
        REPO_ROOT=os.path.abspath(os.path.dirname(__file__)),
    )
