import re

from uncms.media.filetypes import (
    IMAGE_FILENAME_REGEX,
    get_icon,
    get_icon_for_extension,
    is_image,
)


def test_is_image():
    assert is_image('cms.png') is True
    assert is_image('cms.jpg') is True
    assert is_image('cms.jpeg') is True
    assert is_image('cms.gif') is True
    assert is_image('cms.pdf') is False


def test_get_icon():
    assert get_icon('cms.png') == '/static/media/img/image-x-generic.png'
    assert get_icon('cms.doc') == '/static/media/img/x-office-document.png'
    assert get_icon('cms.wat') == '/static/media/img/text-x-generic-template.png'


def test_get_icon_for_extension():
    assert get_icon_for_extension('png') == '/static/media/img/image-x-generic.png'
    assert get_icon_for_extension('doc') == '/static/media/img/x-office-document.png'
    assert get_icon_for_extension('wat') == '/static/media/img/text-x-generic-template.png'


def test_image_regex():
    # Our regex is generated, and it is ugly.
    file_re = re.compile(IMAGE_FILENAME_REGEX)
    assert bool(file_re.search('example.png')) is True
    assert bool(file_re.search('example.jpg')) is True

    # ensure it doesn't work on non-image file types
    assert bool(file_re.search('example.pdf')) is False
    # ensure "." is being treated as a literal
    assert bool(file_re.search('example.gigapng')) is False
    # ensure it only works at the end of a string
    assert bool(file_re.search('example.png2')) is False
    assert bool(file_re.search('example.png.docx')) is False
