from uncms.media.types import MultiThumbnail, Thumbnail


def test_thumbnail_aspect_ratio_string():
    thumbnail = Thumbnail(width=320, height=240, url='fake')
    assert thumbnail.aspect_ratio_string == '320 / 240'


def test_thumbnail_height_ratio():
    thumbnail = Thumbnail(width=400, height=300, url='fake')
    assert thumbnail.height_ratio == 0.75


def test_thumbnail_width_ratio():
    thumbnail = Thumbnail(width=400, height=200, url='fake')
    assert thumbnail.width_ratio == 2


def test_multithumbnail_add_size():
    thumbnail = MultiThumbnail()
    thumbnail.add_size('image/webp', Thumbnail(width=400, height=200, url='/fake-400-webp/'))

    assert len(thumbnail.formats['image/webp'].sizes) == 1

    thumbnail.add_size('image/webp', Thumbnail(width=400, height=200, url='/fake-400-webp/'))
    assert len(thumbnail.formats['image/webp'].sizes) == 1

    thumbnail.add_size('image/webp', Thumbnail(width=400, height=201, url='/fake-400-webp-3/'))
    assert len(thumbnail.formats['image/webp'].sizes) == 1

    thumbnail.add_size('image/webp', Thumbnail(width=800, height=400, url='/fake-800-webp/'))
    assert len(thumbnail.formats['image/webp'].sizes) == 2

    thumbnail.add_size('image/jpeg', Thumbnail(width=800, height=400, url='/fake-800-jpeg/'))
    assert len(thumbnail.formats['image/jpeg'].sizes) == 1
    assert len(thumbnail.formats['image/webp'].sizes) == 2
