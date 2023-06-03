from uncms.media.filetypes import get_icon, get_icon_for_extension, is_image


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
