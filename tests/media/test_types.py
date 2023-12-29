from uncms.media.types import MultiThumbnail, Thumbnail, ThumbnailGroup


def test_thumbnail_aspect_ratio_string():
    thumbnail = Thumbnail(width=320, height=240, url="fake")
    assert thumbnail.aspect_ratio_string == "320 / 240"


def test_thumbnail_height_ratio():
    thumbnail = Thumbnail(width=400, height=300, url="fake")
    assert thumbnail.height_ratio == 0.75


def test_thumbnail_width_ratio():
    thumbnail = Thumbnail(width=400, height=200, url="fake")
    assert thumbnail.width_ratio == 2


def test_multithumbnail_add_size():
    thumbnail = MultiThumbnail()
    thumbnail.add_size(
        "image/webp", Thumbnail(width=400, height=200, url="/fake-400-webp/")
    )

    assert len(thumbnail.formats["image/webp"].sizes) == 1

    thumbnail.add_size(
        "image/webp", Thumbnail(width=400, height=200, url="/fake-400-webp/")
    )
    assert len(thumbnail.formats["image/webp"].sizes) == 1

    thumbnail.add_size(
        "image/webp", Thumbnail(width=400, height=201, url="/fake-400-webp-3/")
    )
    assert len(thumbnail.formats["image/webp"].sizes) == 1

    thumbnail.add_size(
        "image/webp", Thumbnail(width=800, height=400, url="/fake-800-webp/")
    )
    assert len(thumbnail.formats["image/webp"].sizes) == 2

    thumbnail.add_size(
        "image/jpeg", Thumbnail(width=800, height=400, url="/fake-800-jpeg/")
    )
    assert len(thumbnail.formats["image/jpeg"].sizes) == 1
    assert len(thumbnail.formats["image/webp"].sizes) == 2


def test_thumbnailgroup_srcset():
    group = ThumbnailGroup()
    group.add(Thumbnail(width=400, height=200, url="/fake-400-webp/"))
    group.add(Thumbnail(width=600, height=200, url="/fake-600-webp/"))

    srcset = group.srcset
    parts = srcset.split(", ")
    assert len(parts) == 2
    for part in parts[0], parts[1]:
        smaller_parts = part.split(" ")
        assert len(smaller_parts) == 2
        assert smaller_parts[0].startswith("/fake-")
        assert smaller_parts[1].endswith("w")
        assert int(smaller_parts[1].rstrip("w"))

    group = ThumbnailGroup()
    group.add(Thumbnail(width=400, height=200, url="/fake-400-webp/"))
    assert group.srcset == "/fake-400-webp/"
