from django.test import override_settings

from uncms.utils import canonicalise_url


@override_settings(UNCMS={'SITE_DOMAIN': 'canonicalise.example.com'})
def test_get_canonical_url():
    assert canonicalise_url() == 'https://canonicalise.example.com/'

    assert canonicalise_url('/air/') == 'https://canonicalise.example.com/air/'

    with override_settings(DEBUG=True):
        assert canonicalise_url('/air/') == 'http://canonicalise.example.com/air/'

    with override_settings(PREPEND_WWW=True):
        assert canonicalise_url('/air/') == 'https://www.canonicalise.example.com/air/'
