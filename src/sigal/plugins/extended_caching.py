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
a gallery has been built it caches all metadata for all media (markdown, exif,
itpc) in the gallery target folder. Before the next run it restores them so
that the image and metadata files do not have to be parsed again. For large
galleries this can speed up the creation of index files dramatically.
"""

import logging
import os
import pickle

from .. import signals
from ..utils import get_mod_date

logger = logging.getLogger(__name__)


def _cache_key_global(path, name):
    """Global (gallery) cache key function"""
    return os.path.join(path, name)


def _cache_key_local(_, name):
    """Local (album) cache key function"""
    return name


def load_metadata(album):
    """Loads the metadata of all media in an album from cache"""
    plugin_settings = album.gallery.settings.get("extended_caching_options", {})
    if plugin_settings.get("global_cache", True):
        if not hasattr(album.gallery, "metadata_cache"):
            logger.debug("Loading from global gallery cache")
            cache_path = os.path.join(album.gallery.settings["destination"], ".metadata_cache")
            _restore_cache(cache_path, album.gallery)
        cache = album.gallery.metadata_cache
        cache_key = _cache_key_global
    else:
        if not hasattr(album, "metadata_cache"):
            logger.debug("Loading from local album cache %s", album.name)
            _restore_cache(os.path.join(album.dst_path, ".metadata_cache"), album)
        cache = album.metadata_cache
        cache_key = _cache_key_local

    # load album metadata
    key = cache_key(album.path, "_index")
    if key in cache:
        data = cache[key]

        # check if file has changed
        try:
            mod_date = int(get_mod_date(album.markdown_metadata_filepath))
        except FileNotFoundError:
            pass
        else:
            if data.get("mod_date", -1) >= mod_date:
                # cache is good
                if "markdown_metadata" in data:
                    album.markdown_metadata = data["markdown_metadata"]

    # load media metadata
    for media in album.medias:
        key = cache_key(media.path, media.dst_filename)
        if key in cache:
            data = cache[key]

            # check if files have changed
            try:
                mod_date = int(get_mod_date(media.src_path))
            except FileNotFoundError:
                continue
            if data.get("mod_date", -1) < mod_date:
                continue  # file_metadata needs updating

            if "file_metadata" in data:
                media.file_metadata = data["file_metadata"]
            if "exif" in data:
                media.exif = data["exif"]
            if "input_size" in data:
                media.input_size = data["input_size"]

            try:
                mod_date = int(get_mod_date(media.markdown_metadata_filepath))
            except FileNotFoundError:
                continue
            if data.get("meta_mod_date", -1) < mod_date:
                continue  # markdown_metadata needs updating

            if "markdown_metadata" in data:
                media.markdown_metadata = data["markdown_metadata"]


def _restore_cache(cache_path, cache_object):
    """Restores the metadata cache from the cache file"""
    try:
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as cache_file:
                cache_object.metadata_cache = pickle.load(cache_file)
                logger.debug("Loaded cache with %d entries", len(cache_object.metadata_cache))
        else:
            cache_object.metadata_cache = {}
    except Exception as e:
        logger.warning("Could not load cache: %s", e)
        cache_object.metadata_cache = {}


def store_metadata(gallery):
    """Stores the exif data of all images in the gallery"""
    plugin_settings = gallery.settings.get("extended_caching_options", {})
    global_cache = plugin_settings.get("global_cache", True)
    if global_cache:
        logger.debug("Using global gallery cache")
        if not hasattr(gallery, "metadata_cache"):
            gallery.metadata_cache = {}
        cache_key = _cache_key_global
    else:
        logger.debug("Using local album caches")
        cache_key = _cache_key_local

    for album in gallery.albums.values():
        if global_cache:
            cache = gallery.metadata_cache
        else:
            if not hasattr(album, "metadata_cache"):
                album.metadata_cache = {}
            cache = album.metadata_cache

        try:
            data = {
                "mod_date": int(get_mod_date(album.markdown_metadata_filepath)),
                "markdown_metadata": album.markdown_metadata,
            }
            cache[cache_key(album.path, "_index")] = data
        except FileNotFoundError:
            pass

        for media in album.medias:
            data = {}
            try:
                mod_date = int(get_mod_date(media.src_path))
            except FileNotFoundError:
                continue
            else:
                data["mod_date"] = mod_date
                data["file_metadata"] = media.file_metadata
                if hasattr(media, "exif"):
                    data["exif"] = media.exif
                if hasattr(media, "input_size"):
                    data["input_size"] = media.input_size

            try:
                meta_mod_date = int(get_mod_date(media.markdown_metadata_filepath))
            except FileNotFoundError:
                pass
            else:
                data["meta_mod_date"] = meta_mod_date
                data["markdown_metadata"] = media.markdown_metadata

            cache[cache_key(media.path, media.dst_filename)] = data

        if not global_cache:
            cache_path = os.path.join(album.dst_path, ".metadata_cache")
            _save_cache(cache_path, cache)

    if global_cache:
        cache_path = os.path.join(gallery.settings["destination"], ".metadata_cache")
        _save_cache(cache_path, gallery.metadata_cache)


def _save_cache(cache_path, cache):
    """Stores the metadata cache to the cache file"""
    if len(cache) == 0:
        if os.path.exists(cache_path):
            os.remove(cache_path)
        return

    try:
        with open(cache_path, "wb") as cache_file:
            pickle.dump(cache, cache_file)
            logger.debug("Stored cache with %d entries", len(cache))
    except Exception as e:
        logger.warn("Could not store cache: %s", e)
        os.remove(cache_path)


def register(settings):
    signals.gallery_build.connect(store_metadata)
    signals.album_initialized.connect(load_metadata)
