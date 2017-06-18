# encoding: utf-8

# Copyright 2017 - Tilman 't.animal' Adler

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

""" Decreases the time needed to build large galleries (e.g.: 25k images in
2.5s instead of 30s)

This plugin allows extended caching, which is useful for large galleries. Once
a gallery has been built it caches the exif-data of the contained images in the
gallery target folder.  Before the next run it restores them so that the image
does not have to be parsed again. For large galleries this can speed up the
creation of index files dramatically.

"""

import pickle
import logging
import os
from sigal import signals

logger = logging.getLogger(__name__)


def load_exif(album):
    """Loads the exif data of all images in an album from cache"""
    if not hasattr(album.gallery, "exifCache"):
        _restore_cache(album.gallery)
    cache = album.gallery.exifCache

    for media in album.medias:
        if media.type == "image":
            key = os.path.join(media.path, media.filename)
            if key in cache:
                media.exif = cache[key]


def _restore_cache(gallery):
    """Restores the exif data cache from the cache file"""
    cachePath = os.path.join(gallery.settings["destination"], ".exif_cache")
    try:
        if os.path.exists(cachePath):
            with open(cachePath, "rb") as cacheFile:
                gallery.exifCache = pickle.load(cacheFile)
                logger.debug("Loaded cache with %d entries", len(gallery.exifCache))
        else:
            gallery.exifCache = {}
    except Exception as e:
        logger.warn("Could not load cache: %s", e)
        gallery.exifCache = {}


def save_cache(gallery):
    """Stores the exif data of all images in the gallery"""

    if hasattr(gallery, "exifCache"):
        cache = gallery.exifCache
    else:
        cache = gallery.exifCache = {}

    for album in gallery.albums.values():
        for image in album.images:
            cache[os.path.join(image.path, image.filename)] = image.exif

    cachePath = os.path.join(gallery.settings["destination"], ".exif_cache")

    if len(cache) == 0:
        if os.path.exists(cachePath):
            os.remove(cachePath)
        return

    try:
        with open(cachePath, "wb") as cacheFile:
            pickle.dump(cache, cacheFile)
            logger.debug("Stored cache with %d entries", len(gallery.exifCache))
    except Exception as e:
        logger.warn("Could not store cache: %s", e)
        os.remove(cachePath)


def register(settings):
    signals.gallery_build.connect(save_cache)
    signals.album_initialized.connect(load_exif)
