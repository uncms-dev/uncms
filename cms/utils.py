from urllib.parse import urlparse

from django.conf import settings


def canonicalise_url(path=None):
    if path is None:
        path = '/'
    parsed = urlparse(path)

    if settings.PREPEND_WWW:
        domain = f'www.{settings.SITE_DOMAIN}'
    else:
        domain = settings.SITE_DOMAIN

    parsed = parsed._replace(netloc=domain)

    if settings.DEBUG:
        parsed = parsed._replace(scheme='http')

    else:
        parsed = parsed._replace(scheme='https')

    return parsed.geturl()
