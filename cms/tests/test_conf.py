from django.conf import settings
from django.test.utils import override_settings

import cms.conf


def test_conf_get_attr():
    # Check that not having UNCMS present at all gives the correct result.
    with override_settings():
        del settings.UNCMS
        assert cms.conf.defaults.MEDIA_FILE_MODEL == 'media.File'

    # Check that having it as an empty dict returns the correct result.
    with override_settings(UNCMS={}):
        assert cms.conf.defaults.MEDIA_FILE_MODEL == 'media.File'

    # Check that an override works.
    with override_settings(UNCMS={'MEDIA_FILE_MODEL': 'imaginary.File'}):
        assert cms.conf.defaults.MEDIA_FILE_MODEL == 'imaginary.File'
