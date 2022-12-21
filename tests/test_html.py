import pytest
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings

from tests.media.factories import SamplePNGFileFactory
from uncms.html import clean_all, clean_html, format_html
from uncms.media.models import File


@pytest.mark.django_db
def test_format_html():
    image = SamplePNGFileFactory()
    image_with_alt = SamplePNGFileFactory(alt_text='Alt text &')

    old_prefix = f'/r/{ContentType.objects.get_for_model(File).id}-'

    # Test some validation branches.
    html = (
        # No "src" attribute should not cause an exception.
        '<p><img></p>'
        # This will be ignored because it doesn't start with the right prefix.
        '<p><img src="/nothing.jpg"></p>'
        # This will be ignored because it's a non-int PK.
        f'<p><img src="{old_prefix}nonsense"></p>'
        # This will be ignored because pk #0 can't exist.
        f'<p><img src="{old_prefix}0"></p>'
    )

    assert format_html(html).strip() == (
        '<p><img/></p>'
        '<p><img src="/nothing.jpg"/></p>'
        f'<p><img src="{old_prefix}nonsense"/></p>'
        f'<p><img src="{old_prefix}0"/></p>'
    )

    html = (
        # Test with no alt text to ensure it gets an empty string and not
        # None or a missing value
        f'<p><img title="&amp;" src="{old_prefix}{image.pk}"></p>'
        # Test copying alt text onto the image.
        f'<p><img src="{old_prefix}{image_with_alt.pk}"></p>'
        # Don't overwrite an existing alt text.
        f'<p><img alt="Override" src="{old_prefix}{image_with_alt.pk}"></p>'
    )

    assert format_html(html).strip() == (
        f'<p><img alt="" src="{image.file.url}" title="&amp;"/></p>'
        f'<p><img alt="Alt text &amp;" src="{image_with_alt.file.url}"/></p>'
        f'<p><img alt="Override" src="{image_with_alt.file.url}"/></p>'
    )


def example_processor(html):
    # sample processor for testing config overrides
    return html.replace('woof', 'meow')


def test_html_clean():
    html = '<script>alert("Hello!")><img loading="lazy" onload="alert(&quot;whoops&quot;)" title="example" class="test" src="/example.png"><p>woof</p>'

    for clean_func in clean_html, clean_all:
        assert clean_func(html) == '&lt;script&gt;alert("Hello!")&gt;<img loading="lazy" title="example" class="test" src="/example.png"><p>woof</p>'

    # check settings overrides work
    with override_settings(UNCMS={'HTML_CLEANERS': ['uncms.html.clean_html', 'tests.test_html.example_processor']}):
        assert clean_all(html) == '&lt;script&gt;alert("Hello!")&gt;<img loading="lazy" title="example" class="test" src="/example.png"><p>meow</p>'
