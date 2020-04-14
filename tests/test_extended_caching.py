import os
import pickle

from sigal.gallery import Gallery
from sigal.plugins import extended_caching

CURRENT_DIR = os.path.dirname(__file__)


def test_save_cache(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    gal = Gallery(settings, ncpu=1)
    extended_caching.save_cache(gal)

    cachePath = os.path.join(settings['destination'], ".exif_cache")

    assert os.path.isfile(cachePath)

    with open(cachePath, "rb") as cacheFile:
        cache = pickle.load(cacheFile)

    assert cache["exifTest/21.jpg"] == gal.albums["exifTest"].medias[0].exif
    assert cache["exifTest/22.jpg"] == gal.albums["exifTest"].medias[1].exif
    assert cache["exifTest/noexif.png"] == gal.albums["exifTest"].medias[2].exif


def test_restore_cache(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    gal1 = Gallery(settings, ncpu=1)
    gal2 = Gallery(settings, ncpu=1)
    extended_caching.save_cache(gal1)
    extended_caching._restore_cache(gal2)
    assert gal1.exifCache == gal2.exifCache


def test_load_exif(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    gal1 = Gallery(settings, ncpu=1)
    gal1.albums["exifTest"].medias[2].exif = "blafoo"
    gal1.exifCache = {"exifTest/21.jpg": "Foo",
                      "exifTest/22.jpg": "Bar"}

    extended_caching.load_exif(gal1.albums["exifTest"])

    assert gal1.albums["exifTest"].medias[0].exif == "Foo"
    assert gal1.albums["exifTest"].medias[1].exif == "Bar"
    assert gal1.albums["exifTest"].medias[2].exif == "blafoo"

    # check if setting gallery.exifCache works
    gal2 = Gallery(settings, ncpu=1)
    extended_caching.save_cache(gal1)
    extended_caching.load_exif(gal2.albums["exifTest"])
