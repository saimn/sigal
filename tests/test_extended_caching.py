import os
import pickle

from sigal.gallery import Gallery, Image
from sigal.plugins import extended_caching

CURRENT_DIR = os.path.dirname(__file__)


def test_save_cache(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    gal = Gallery(settings, ncpu=1)
    extended_caching.save_cache(gal)

    cachePath = os.path.join(settings['destination'], ".metadata_cache")

    assert os.path.isfile(cachePath)

    with open(cachePath, "rb") as cacheFile:
        cache = pickle.load(cacheFile)

    # test exif
    album = gal.albums["exifTest"]
    cache_img = cache["exifTest/21.jpg"]
    assert cache_img["exif"] == album.medias[0].exif
    assert 'markdown_metadata' not in cache_img
    assert cache_img["file_metadata"] == album.medias[0].file_metadata

    cache_img = cache["exifTest/22.jpg"]
    assert cache_img["exif"] == album.medias[1].exif
    assert 'markdown_metadata' not in cache_img
    assert cache_img["file_metadata"] == album.medias[1].file_metadata

    cache_img = cache["exifTest/noexif.png"]
    assert cache_img["exif"] == album.medias[2].exif
    assert 'markdown_metadata' not in cache_img
    assert cache_img["file_metadata"] == album.medias[2].file_metadata

    # test iptc and md
    album = gal.albums["iptcTest"]
    assert cache["iptcTest/_index"]["markdown_metadata"] == album.markdown_metadata

    cache_img = cache["iptcTest/1.jpg"]
    assert cache_img["file_metadata"] == album.medias[0].file_metadata
    assert 'markdown_metadata' not in cache_img

    cache_img = cache["iptcTest/2.jpg"]
    assert cache_img["markdown_metadata"] == album.medias[1].markdown_metadata

    # test if file disappears
    gal.albums["exifTest"].medias.append(Image("foooo.jpg", "exifTest", settings))
    extended_caching.save_cache(gal)
    with open(cachePath, "rb") as cacheFile:
        cache = pickle.load(cacheFile)
    assert "exifTest/foooo.jpg" not in cache


def test_restore_cache(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    gal1 = Gallery(settings, ncpu=1)
    gal2 = Gallery(settings, ncpu=1)
    extended_caching.save_cache(gal1)
    extended_caching._restore_cache(gal2)
    assert gal1.metadataCache == gal2.metadataCache

    # test bad cache
    cachePath = os.path.join(settings['destination'], ".metadata_cache")
    with open(cachePath, 'w') as f:
        f.write('bad pickle file')

    extended_caching._restore_cache(gal2)
    assert gal2.metadataCache == {}


def test_load_exif(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    gal1 = Gallery(settings, ncpu=1)
    gal1.albums["exifTest"].medias[2].exif = "blafoo"
    # set mod_date in future, to force these values
    gal1.metadataCache = {
        "exifTest/21.jpg": {"exif": "Foo", "mod_date": 100000000000},
        "exifTest/22.jpg": {"exif": "Bar", "mod_date": 100000000000},
    }

    extended_caching.load_metadata(gal1.albums["exifTest"])

    assert gal1.albums["exifTest"].medias[0].exif == "Foo"
    assert gal1.albums["exifTest"].medias[1].exif == "Bar"
    assert gal1.albums["exifTest"].medias[2].exif == "blafoo"

    # check if setting gallery.metadataCache works
    gal2 = Gallery(settings, ncpu=1)
    extended_caching.save_cache(gal1)
    extended_caching.load_metadata(gal2.albums["exifTest"])

    assert gal2.albums["exifTest"].medias[0].exif == "Foo"
    assert gal2.albums["exifTest"].medias[1].exif == "Bar"
    assert gal2.albums["exifTest"].medias[2].exif == "blafoo"


def test_load_metadata_missing(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    gal = Gallery(settings, ncpu=1)
    extended_caching.save_cache(gal)
    assert gal.metadataCache

    # test if file disappears
    gal.albums["exifTest"].medias.append(Image("foooo.jpg", "exifTest", settings))

    # set mod_date to -1 to force cache update
    gal.metadataCache = {
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
