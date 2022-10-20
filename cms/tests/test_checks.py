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
