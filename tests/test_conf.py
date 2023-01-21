import os.path

from django.conf import settings
from django.test.utils import override_settings

import uncms.conf


def test_conf_get_attr():
    # Check that not having UNCMS present at all gives the correct result.
    with override_settings():
        del settings.UNCMS
        assert uncms.conf.defaults.MEDIA_FILE_MODEL == 'media.File'

    # Check that having it as an empty dict returns the correct result.
    with override_settings(UNCMS={}):
        assert uncms.conf.defaults.MEDIA_FILE_MODEL == 'media.File'

    # Check that an override works.
    with override_settings(UNCMS={'MEDIA_FILE_MODEL': 'imaginary.File'}):
        assert uncms.conf.defaults.MEDIA_FILE_MODEL == 'imaginary.File'


def test_conf_get_wysiwyg_options():
    assert uncms.conf.defaults.get_wysiwyg_options()['resetCss'] is True
    with override_settings(UNCMS={'WYSIWYG_EXTRA_OPTIONS': {'resetCss': False, 'nonsense': True}}):
        assert uncms.conf.defaults.get_wysiwyg_options()['resetCss'] is False
        assert uncms.conf.defaults.get_wysiwyg_options()['nonsense'] is True


def test_all_config_items_are_documented():
    """
    Ensure all configuration items are documented in docs/configuration.md
    and that no imaginary options are in the documentation.

    This is a relatively dumb test but it should work well enough :)
    """
    with open(os.path.join(settings.REPO_ROOT, 'docs', 'configuration.md'), encoding='utf-8') as fd:
        items = [
            # as i said, not a smart test...
            line.replace('##', '').replace('`', '').strip()
            for line in fd
            if line.startswith('## `')
        ]

    assert list(set(items)) == list(set(uncms.conf.defaults.default_settings.keys())), 'undocumented settings and/or imaginary documented settings'
