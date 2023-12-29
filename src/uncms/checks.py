import re

from django.conf import settings
from django.core import checks
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _

from uncms.conf import defaults


@checks.register()
def check_site_domain(app_configs, **kwargs):
    if not defaults.SITE_DOMAIN:
        return [
            checks.Error(
                'UNCMS["SITE_DOMAIN"] must not be empty or None',
                hint=(
                    "Put this in your Django settings:\n\n"
                    "UNCMS = {\n"
                    '    "SITE_DOMAIN": "example.com",\n'
                    "}"
                ),
                id="uncms.001",
            )
        ]
    return []


@checks.register
def check_publication_middleware_exclude_urls(app_configs, **kwargs):
    errors = []
    # easy misconfiguration option that can cause everything to break
    if not isinstance(defaults.PUBLICATION_MIDDLEWARE_EXCLUDE_URLS, (list, tuple)):
        errors.append(
            checks.Error(
                _(
                    'UNCMS["PUBLICATION_MIDDLEWARE_EXCLUDE_URLS"] must be a list or tuple'
                ),
                id="uncms.003",
            )
        )

    try:
        admin_url = reverse("admin:index")
    # They're not using the Django admin, so like, OK.
    except NoReverseMatch:  # pragma: no cover
        pass
    else:
        is_excluded = any(
            re.match(item, admin_url)
            for item in defaults.PUBLICATION_MIDDLEWARE_EXCLUDE_URLS
        )
        if not is_excluded:
            errors.append(
                checks.Error(
                    _(
                        '"{path}" does not seem to be excluded from publication management by UNCMS["PUBLICATION_MIDDLEWARE_EXCLUDE_URLS"]. This will make it impossible to edit offline objects!'
                    ).format(path=admin_url),
                    id="uncms.003",
                )
            )
    return errors


@checks.register
def check_django_settings(app_configs, **kwargs):
    errors = []
    required_middleware = [
        "uncms.middleware.PublicationMiddleware",
        "uncms.pages.middleware.PageMiddleware",
    ]
    for middleware in required_middleware:
        if middleware not in settings.MIDDLEWARE:
            errors.append(
                checks.Error(
                    _(
                        "'{middleware}' must be in settings.MIDDLEWARE for UnCMS to work"
                    ).format(middleware=middleware),
                    id="uncms.004",
                )
            )

    for template_engine in settings.TEMPLATES:
        processors = template_engine.get("OPTIONS", {}).get("context_processors", [])
        # This one is required...
        required = "django.template.context_processors.request"
        if required not in processors:
            errors.append(
                checks.Error(
                    _(
                        "'{processor}' must be in your template engine's 'context_processors'."
                    ).format(processor=required),
                    id="uncms.005",
                )
            )
        # ...and this one is not, but we usually refer to "pages" rather than
        # "request.pages" in the docs, so we'll just warn for that.
        recommended = "uncms.pages.context_processors.pages"
        if recommended not in processors:
            errors.append(
                checks.Warning(
                    _(
                        "'{processor}' should be in your template engine's 'context_processors'."
                    ).format(processor=recommended),
                    id="uncms.006",
                )
            )

    # Setting MEDIA_URL to '/' (which is the default for `startproject`) will
    # stop the page system from working. PageMiddleware skips any requests
    # that start with MEDIA_URL, and all paths begin with '/'!
    if settings.MEDIA_URL == "/":
        errors.append(
            checks.Error(
                _(
                    "`MEDIA_URL` is set to `/`, which will cause the page middleware to be non-functional."
                ),
                id="uncms.007",
                hint=_(
                    "Set it to the public path for file uploads (see the Django documentation)."
                ),
            )
        )
    return errors
