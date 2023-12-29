import getpass
import os

import pytest
from django.conf import settings

DJANGO_TEMPLATE_CONFIG = {
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [
        os.path.join("uncms", "tests", "templates"),
    ],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.contrib.auth.context_processors.auth",
            "django.template.context_processors.debug",
            "django.template.context_processors.i18n",
            "django.template.context_processors.media",
            "django.template.context_processors.static",
            "django.contrib.messages.context_processors.messages",
            "django.template.context_processors.request",
            "uncms.pages.context_processors.pages",
        ]
    },
}


def pytest_configure():
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": os.environ.get(
                    "UNCMS_DB_BACKEND", "django.db.backends.postgresql"
                ),
                "NAME": os.environ.get("UNCMS_DB_NAME", "uncms_test"),
                "USER": os.environ.get("UNCMS_DB_USER", getpass.getuser()),
                "PASSWORD": os.environ.get("UNCMS_DB_PASSWORD"),
                "TEST": {
                    "NAME": "uncms_test",
                },
            }
        },
        STATIC_URL="/static/",
        MEDIA_URL="/media/",
        MEDIA_ROOT=os.path.join(os.path.dirname(__file__), "media/"),
        INSTALLED_APPS=[
            # Django apps
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.messages",
            "django.contrib.sessions",
            "django.contrib.sitemaps",
            # CMS apps
            "uncms",
            "uncms.links",
            "uncms.media",
            "uncms.pages",
            "uncms.redirects",
            "uncms.testhelpers",
            # Testing models & such
            "tests.testing_app",
            # Third party apps
            "sorl.thumbnail",
            "reversion",
            "watson",
        ],
        ROOT_URLCONF="tests.urls",
        ALLOWED_HOSTS=["*"],
        TEMPLATES=[DJANGO_TEMPLATE_CONFIG],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            "uncms.middleware.PublicationMiddleware",
            "uncms.pages.middleware.PageMiddleware",
            "watson.middleware.SearchContextMiddleware",
        ],
        SECRET_KEY="KNOWN_FIXED_VALUE_IS_FINE",
        UNCMS={
            "SITE_DOMAIN": "example.com",
        },
        THUMBNAIL_PRESERVE_FORMAT=True,
        REPO_ROOT=os.path.abspath(os.path.dirname(__file__)),
        X_FRAME_OPTIONS="DENY",
    )


@pytest.fixture
def use_jinja2(settings):
    settings.TEMPLATES = [
        DJANGO_TEMPLATE_CONFIG,
        {
            "BACKEND": "django.template.backends.jinja2.Jinja2",
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.contrib.auth.context_processors.auth",
                    "django.template.context_processors.debug",
                    "django.template.context_processors.i18n",
                    "django.template.context_processors.media",
                    "django.template.context_processors.static",
                    "django.contrib.messages.context_processors.messages",
                    "django.template.context_processors.request",
                    "uncms.pages.context_processors.pages",
                ],
                "environment": "uncms.jinja2_environment.all.environment",
            },
        },
    ]
