import os
import pickle

from sigal.gallery import Gallery, Image
from sigal.plugins import extended_caching

CURRENT_DIR = os.path.dirname(__file__)


def test_store_metadata(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    gal = Gallery(settings, ncpu=1)
    extended_caching.store_metadata(gal)

    cache_path = os.path.join(settings["destination"], ".metadata_cache")

    assert os.path.isfile(cache_path)

    with open(cache_path, "rb") as cacheFile:
        cache = pickle.load(cacheFile)

    # test exif
    album = gal.albums["exifTest"]
    media = next(m for m in album.medias if m.src_filename == "21.jpg")
    cache_img = cache["exifTest/21.jpg"]
    assert cache_img["exif"] == media.exif
    assert "markdown_metadata" not in cache_img
    assert cache_img["file_metadata"] == media.file_metadata

    media = next(m for m in album.medias if m.src_filename == "22.jpg")
    cache_img = cache["exifTest/22.jpg"]
    assert cache_img["exif"] == media.exif
    assert "markdown_metadata" not in cache_img
    assert cache_img["file_metadata"] == media.file_metadata

    media = next(m for m in album.medias if m.src_filename == "noexif.png")
    cache_img = cache["exifTest/noexif.png"]
    assert cache_img["exif"] == media.exif
    assert "markdown_metadata" not in cache_img
    assert cache_img["file_metadata"] == media.file_metadata

    # test iptc and md
    album = gal.albums["iptcTest"]
    assert cache["iptcTest/_index"]["markdown_metadata"] == album.markdown_metadata

    cache_img = cache["iptcTest/1.jpg"]
    assert cache_img["file_metadata"] == album.medias[0].file_metadata
    assert "markdown_metadata" not in cache_img

    cache_img = cache["iptcTest/2.jpg"]
    assert cache_img["markdown_metadata"] == album.medias[1].markdown_metadata

    # test if file disappears
    gal.albums["exifTest"].medias.append(Image("foooo.jpg", "exifTest", settings))
    extended_caching.store_metadata(gal)
    with open(cache_path, "rb") as cacheFile:
        cache = pickle.load(cacheFile)
    assert "exifTest/foooo.jpg" not in cache


def test_load_metadata(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    gal1 = Gallery(settings, ncpu=1)
    gal2 = Gallery(settings, ncpu=1)
    extended_caching.store_metadata(gal1)
    for album in gal2.albums.values():
        extended_caching.load_metadata(album)
        break  # only need to load one
    assert gal1.metadata_cache == gal2.metadata_cache


def test_restore_cache(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    gal1 = Gallery(settings, ncpu=1)
    gal2 = Gallery(settings, ncpu=1)
    extended_caching.store_metadata(gal1)
    cache_path = os.path.join(settings["destination"], ".metadata_cache")
    extended_caching._restore_cache(cache_path, gal2)
    assert gal1.metadata_cache == gal2.metadata_cache

    # test bad cache
    with open(cache_path, "w") as f:
        f.write("bad pickle file")

    extended_caching._restore_cache(cache_path, gal2)
    assert gal2.metadata_cache == {}


def test_store_metadata_local(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    settings['extended_caching_options'] = {'global_cache': False}
    gal = Gallery(settings, ncpu=1)
    extended_caching.store_metadata(gal)

    for album in gal.albums.values():
        if album.metadata_cache:
            cache_path = os.path.join(album.dst_path, ".metadata_cache")
            assert os.path.isfile(cache_path)
            with open(cache_path, "rb") as cacheFile:
                cache = pickle.load(cacheFile)

    # test exif
    cache_path = os.path.join(settings["destination"], "exifTest", ".metadata_cache")
    assert os.path.isfile(cache_path)
    with open(cache_path, "rb") as cacheFile:
        cache = pickle.load(cacheFile)

    album = gal.albums["exifTest"]
    cache_img = cache["21.jpg"]
    assert cache_img["exif"] == album.medias[0].exif
    assert "markdown_metadata" not in cache_img
    assert cache_img["file_metadata"] == album.medias[0].file_metadata

    cache_img = cache["22.jpg"]
    assert cache_img["exif"] == album.medias[1].exif
    assert "markdown_metadata" not in cache_img
    assert cache_img["file_metadata"] == album.medias[1].file_metadata

    cache_img = cache["noexif.png"]
    assert cache_img["exif"] == album.medias[2].exif
    assert "markdown_metadata" not in cache_img
    assert cache_img["file_metadata"] == album.medias[2].file_metadata

    # test iptc and md
    cache_path = os.path.join(settings["destination"], "iptcTest", ".metadata_cache")
    assert os.path.isfile(cache_path)
    with open(cache_path, "rb") as cacheFile:
        cache = pickle.load(cacheFile)

    album = gal.albums["iptcTest"]
    assert cache["_index"]["markdown_metadata"] == album.markdown_metadata

    cache_img = cache["1.jpg"]
    assert cache_img["file_metadata"] == album.medias[0].file_metadata
    assert "markdown_metadata" not in cache_img

    cache_img = cache["2.jpg"]
    assert cache_img["markdown_metadata"] == album.medias[1].markdown_metadata

    # test if file disappears
    gal.albums["exifTest"].medias.append(Image("foooo.jpg", "exifTest", settings))
    extended_caching.store_metadata(gal)
    cache_path = os.path.join(settings["destination"], "exifTest", ".metadata_cache")
    with open(cache_path, "rb") as cacheFile:
        cache = pickle.load(cacheFile)
    assert "foooo.jpg" not in cache


def test_restore_cache_local(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    settings['extended_caching_options'] = {'global_cache': False}
    gal1 = Gallery(settings, ncpu=1)
    gal2 = Gallery(settings, ncpu=1)
    extended_caching.store_metadata(gal1)
    cache_path = os.path.join(settings["destination"], "exifTest", ".metadata_cache")
    extended_caching._restore_cache(cache_path, gal2.albums["exifTest"])
    assert not hasattr(gal1, "metadata_cache")
    assert not hasattr(gal2, "metadata_cache")
    assert gal1.albums["exifTest"].metadata_cache == gal2.albums["exifTest"].metadata_cache

    # test bad cache
    with open(cache_path, "w") as f:
        f.write("bad pickle file")

    extended_caching._restore_cache(cache_path, gal2.albums["exifTest"])
    assert gal2.albums["exifTest"].metadata_cache == {}


def test_load_metadata_local(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    settings['extended_caching_options'] = {'global_cache': False}
    gal1 = Gallery(settings, ncpu=1)
    gal2 = Gallery(settings, ncpu=1)
    extended_caching.store_metadata(gal1)
    for album in gal2.albums.values():
        extended_caching.load_metadata(album)
    assert not hasattr(gal1, "metadata_cache")
    assert not hasattr(gal2, "metadata_cache")
    for al1, al2 in zip(gal1.albums.values(), gal2.albums.values()):
        assert al1.metadata_cache == al2.metadata_cache


def test_load_exif(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    gal1 = Gallery(settings, ncpu=1)
    gal1.albums["exifTest"].medias[3].exif = "blafoo"
    # set mod_date in future, to force these values
    gal1.metadata_cache = {
        "exifTest/21.jpg": {"exif": "Foo", "mod_date": 100000000000},
        "exifTest/22.jpg": {"exif": "Bar", "mod_date": 100000000000},
        "exifTest/22-nodate.jpg": {"exif": "Baz", "mod_date": 100000000000},
    }

    extended_caching.load_metadata(gal1.albums["exifTest"])

    def get_media(gal, filename):
        return next(
            m for m in gal.albums["exifTest"].medias if m.src_filename == filename
        )

    assert get_media(gal1, "21.jpg").exif == "Foo"
    assert get_media(gal1, "22.jpg").exif == "Bar"
    assert get_media(gal1, "noexif.png").exif == "blafoo"

    # check if setting gallery.metadata_cache works
    gal2 = Gallery(settings, ncpu=1)
    extended_caching.store_metadata(gal1)
    extended_caching.load_metadata(gal2.albums["exifTest"])

    assert get_media(gal2, "21.jpg").exif == "Foo"
    assert get_media(gal2, "22.jpg").exif == "Bar"
    assert get_media(gal2, "noexif.png").exif == "blafoo"


def test_load_metadata_missing(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    gal = Gallery(settings, ncpu=1)
    extended_caching.store_metadata(gal)
    assert gal.metadata_cache

    # test if file disappears
    gal.albums["exifTest"].medias.append(Image("foooo.jpg", "exifTest", settings))

    # set mod_date to -1 to force cache update
    gal.metadata_cache = {
        "exifTest/_index": {
            "mod_date": -1,
        },
        "exifTest/21.jpg": {"exif": "Foo", "mod_date": -1},
        "exifTest/foooo.jpg": {"exif": "Foo"},
        "dir1/test2/22.jpg": {
            "exif": "Bar",
            "mod_date": 100000000000,
            "meta_mod_date": -1,
            "markdown_metadata": "Bar",
        },
    }
    # errors should all be caught
    extended_caching.load_metadata(gal.albums["exifTest"])
    assert gal.albums["exifTest"].medias[0].exif != "Foo"
    assert gal.albums["exifTest"].medias[-1].exif != "Foo"

    extended_caching.load_metadata(gal.albums["dir1/test2"])
    assert gal.albums["dir1/test2"].medias[1].exif == "Bar"
    assert gal.albums["dir1/test2"].medias[1].markdown_metadata != "Bar"


def test_empty_cache(settings, tmpdir):
    cache_path = os.path.join(tmpdir, ".metadata_cache")
    with open(cache_path, 'w') as f:
        f.write("bad pickle file")
    extended_caching._save_cache(cache_path, {})
    assert not os.path.exists(cache_path)


def test_uncachable(settings, tmpdir):
    cache_path = os.path.join(tmpdir, ".metadata_cache")
    with open(cache_path, 'w') as f:
        f.write("bad pickle file")
    extended_caching._save_cache(cache_path, {'func': lambda x: x+1})
    assert not os.path.exists(cache_path)
