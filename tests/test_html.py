import pytest
from bs4 import BeautifulSoup
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings

from uncms.html import clean_all, clean_html, format_html
from uncms.media.models import File
from uncms.testhelpers.factories.media import SamplePNGFileFactory


@pytest.mark.django_db
def test_format_html():
    image = SamplePNGFileFactory()
    image_with_alt = SamplePNGFileFactory(alt_text='Alt text &')

    old_prefix = f'/r/{ContentType.objects.get_for_model(File).id}-'
    new_prefix = '/library/redirect/'

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
        # This will be ignored because it only starts with the prefix. This
        # should not cause an exception :)
        f'<p><img src="{new_prefix}"></p>'
    )

    assert format_html(html).strip() == (
        '<p><img/></p>'
        '<p><img src="/nothing.jpg"/></p>'
        f'<p><img src="{old_prefix}nonsense"/></p>'
        f'<p><img src="{old_prefix}0"/></p>'
        f'<p><img src="{new_prefix}"/></p>'
    )

    html = (
        # Test with no alt text to ensure it gets an empty string and not
        # None or a missing value. Also, test copying attributes like "title"
        f'<p><img title="&amp;" src="{old_prefix}{image.pk}"></p>'
        # test not being fussy about trailing / in the URL
        f'<p><img src="{old_prefix}{image.pk}/"/></p>'
        # test new-style URL prefixes
        f'<p><img src="{new_prefix}{image.pk}/"></p>'
        # Test copying alt text onto the image.
        f'<p><img src="{old_prefix}{image_with_alt.pk}"></p>'
        # Don't overwrite an existing alt text.
        f'<p><img alt="Override" src="{old_prefix}{image_with_alt.pk}"></p>'
        # Preserve existing style attributes
        f'<p><img src="{old_prefix}{image.pk}" style="transform: rotate(180deg)"></p>'
        # Preserve class attributes
        f'<p><img class="left" src="{old_prefix}{image.pk}"></p>'
    )

    soup = BeautifulSoup(format_html(html), 'html.parser')
    picture_tags = soup.find_all('picture')
    assert len(picture_tags) == 7

    img_tags = [picture_tag.find('img') for picture_tag in picture_tags]

    assert img_tags[0]['title'] == '&'
    assert img_tags[0]['alt'] == ''
    assert img_tags[1]['src'] == image.get_absolute_url()
    assert img_tags[2]['src'] == image.get_absolute_url()
    assert img_tags[3]['alt'] == 'Alt text &'
    assert img_tags[4]['alt'] == 'Override'
    assert img_tags[5]['style'] == 'aspect-ratio: 1280 / 720; transform: rotate(180deg)'
    assert img_tags[6]['class'] == ['image__image', 'left']


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
