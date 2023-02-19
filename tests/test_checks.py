from io import StringIO

from django.core.management import call_command
from django.test.utils import override_settings


def get_command_output(command, *args, **kwargs):
    stdout = StringIO()
    stderr = StringIO()
    call_command(command, *args, stdout=stdout, stderr=stderr, fail_level='CRITICAL', **kwargs)
    return (stdout.getvalue(), stderr.getvalue())


def test_check_publication_middleware_exclude_urls():
    _, stderr = get_command_output('check')
    # empty stderr should mean no issues
    assert stderr == ''

    with override_settings(UNCMS={'SITE_DOMAIN': 'example.com', 'PUBLICATION_MIDDLEWARE_EXCLUDE_URLS': r'^/admin/'}):
        _, stderr = get_command_output('check')
    assert "must be a list or tuple" in stderr
    assert 'uncms.003' in stderr

    with override_settings(UNCMS={'SITE_DOMAIN': 'example.com', 'PUBLICATION_MIDDLEWARE_EXCLUDE_URLS': ['/secretadmin/']}):
        _, stderr = get_command_output('check')
    assert '"/admin/" does not seem to be excluded from publication management' in stderr


def test_check_site_domain():
    _, stderr = get_command_output('check')
    # empty stderr should mean no issues
    assert stderr == ''

    for invalid_value in [None, '']:
        with override_settings(UNCMS={'SITE_DOMAIN': invalid_value}):
            _, stderr = get_command_output('check')
    assert 'UNCMS["SITE_DOMAIN"] must not be empty or None' in stderr
    assert 'uncms.001' in stderr


def test_check_django_settings():
    _, stderr = get_command_output('check')
    # empty stderr should mean no issues
    assert stderr == ''

    look_for = "'uncms.pages.middleware.PageMiddleware' must be in settings.MIDDLEWARE"
    with override_settings(MIDDLEWARE=['django.middleware.common.CommonMiddleware']):
        _, stderr = get_command_output('check')
    assert look_for in stderr
    assert 'uncms.004' in stderr

    bad_template_config = [{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [],
        },
    }]
    with override_settings(TEMPLATES=bad_template_config):
        _, stderr = get_command_output('check')
    assert all(
        message in stderr
        for message in [
            "'django.template.context_processors.request' must be in",
            "'uncms.pages.context_processors.pages' should be in",
            'uncms.005',
            'uncms.006',
        ]
    )

    with override_settings(MEDIA_URL='/'):
        _, stderr = get_command_output('check')
    assert '`MEDIA_URL` is set to `/`' in stderr
    assert 'uncms.007' in stderr
