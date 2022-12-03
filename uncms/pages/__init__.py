from django.apps import apps as django_apps

from uncms.conf import defaults


def get_page_model():
    return django_apps.get_model(defaults.PAGE_MODEL)
