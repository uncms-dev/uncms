from django.core.checks import Error, register

from uncms.conf import defaults


@register()
def check_site_domain(app_configs, **kwargs):
    if not defaults.SITE_DOMAIN:
        return [Error(
            'UNCMS["SITE_DOMAIN"] must not be empty or None',
            hint=(
                "Put this in your Django settings:\n\n"
                'UNCMS = {\n'
                '    "SITE_DOMAIN": "example.com",\n'
                '}'
            ),
            id='uncms.001'
        )]
    return []
