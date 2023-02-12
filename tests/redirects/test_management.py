import os

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from uncms.redirects.models import Redirect


def data_file_path(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


@pytest.mark.django_db
def test_importredirectscsv_dry_run():
    # Make sure dry run is really doing that.
    call_command('import_redirects_csv', data_file_path('redirects_no_header.csv'), '--dry-run')
    assert Redirect.objects.count() == 0

    call_command('import_redirects_csv', data_file_path('redirects_no_header.csv'))
    assert Redirect.objects.count() == 2


@pytest.mark.django_db
def test_importredirectscsv_ignore_errors():
    # file with a header will raise an exception
    with pytest.raises(CommandError) as exc:
        call_command('import_redirects_csv', data_file_path('redirects_with_header.csv'))
    assert 'abandoning import due to errors' in str(exc.value)
    assert Redirect.objects.count() == 0

    # Run again, but tell it to ignore errors and redirects should have been
    # created.
    call_command('import_redirects_csv', data_file_path('redirects_with_header.csv'), '--ignore-errors')
    assert Redirect.objects.count() == 2


@pytest.mark.django_db
def test_importredirectscsv_skip_header():
    call_command('import_redirects_csv', data_file_path('redirects_with_header.csv'), '--skip-header')
    assert Redirect.objects.count() == 2


@pytest.mark.django_db
def test_importredirectscsv_verbosity():
    # Just check our verbosity branches don't raise an exception, the output
    # is not that interesting
    call_command('import_redirects_csv', data_file_path('redirects_no_header.csv'), '--verbosity=2')
    assert Redirect.objects.count() == 2

    call_command('import_redirects_csv', data_file_path('redirects_with_header.csv'), '--verbosity=2', '--ignore-errors')
    assert Redirect.objects.count() == 2
