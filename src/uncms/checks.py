from django.conf import settings
from django.core import checks
from django.utils.translation import gettext_lazy as _

from uncms.conf import defaults


@checks.register()
def check_site_domain(app_configs, **kwargs):
    if not defaults.SITE_DOMAIN:
        return [checks.Error(
            'UNCMS["SITE_DOMAIN"] must not be empty or None',
            hint=(
                "Put this in your Django settings:\n\n"
                'UNCMS = {\n'
                '    "SITE_DOMAIN": "example.com",\n'
                '}'
            ),
            id='uncms.001',
        )]
    return []


@checks.register
def check_django_settings(app_configs, **kwargs):
    errors = []
    required_middleware = [
        'uncms.middleware.PublicationMiddleware',
        'uncms.pages.middleware.PageMiddleware',
    ]
    for middleware in required_middleware:
        if middleware not in settings.MIDDLEWARE:
            errors.append(checks.Error(
                _("'{middleware}' must be in settings.MIDDLEWARE for UnCMS to work").format(middleware=middleware),
                id='uncms.002',
            ))

    for template_engine in settings.TEMPLATES:
        processors = template_engine.get('OPTIONS', {}).get('context_processors', [])
        # This one is required...
        required = 'django.template.context_processors.request'
        if required not in processors:
            errors.append(checks.Error(
                _("'{processor}' must be in your template engine's 'context_processors'.").format(processor=required),
                id='uncms.003',
            ))
        # ...and this one is not, but we usually refer to "pages" rather than
        # "request.pages" in the docs, so we'll just warn for that.
        recommended = 'uncms.pages.context_processors.pages'
        if recommended not in processors:
            errors.append(checks.Warning(
                _("'{processor}' should be in your template engine's 'context_processors'.").format(processor=recommended),
                id='uncms.004',
            ))

    return errors
