from io import StringIO

from django.core.management import call_command
from django.test.utils import override_settings


def get_command_output(command, *args, **kwargs):
    stdout = StringIO()
    stderr = StringIO()
    call_command(command, *args, stdout=stdout, stderr=stderr, fail_level='CRITICAL', **kwargs)
    return (stdout.getvalue(), stderr.getvalue())


def test_check_site_domain():
    look_for = 'UNCMS["SITE_DOMAIN"] must not be empty or None'
    _, stderr = get_command_output('check')
    assert look_for not in stderr

    for invalid_value in [None, '']:
        with override_settings(UNCMS={'SITE_DOMAIN': invalid_value}):
            _, stderr = get_command_output('check')
    assert look_for in stderr
    assert 'uncms.001' in stderr


def test_check_django_settings():
    _, stderr = get_command_output('check')
    # empty stderr should mean no issues
    assert stderr == ''

    look_for = "'uncms.pages.middleware.PageMiddleware' must be in settings.MIDDLEWARE"
    with override_settings(MIDDLEWARE=['django.middleware.common.CommonMiddleware']):
        _, stderr = get_command_output('check')
    assert look_for in stderr
    assert 'uncms.002' in stderr

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
            'uncms.003',
            'uncms.004',
        ]
    )
