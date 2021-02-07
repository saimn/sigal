# copyright (c) 2020 Bowen Ding

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

import logging
import os
import pickle
import random
import string
from io import BytesIO
from itertools import chain

from click import progressbar

from sigal import signals
from sigal.settings import get_thumb
from sigal.utils import copy

from .endec import encrypt, kdf_gen_key

logger = logging.getLogger(__name__)

ASSETS_PATH = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static'))


class Abort(Exception):
    pass


def gen_rand_string(length=16):
    return "".join(random.SystemRandom().choices(string.ascii_letters +
                                                 string.digits,
                                                 k=length))


def get_options(settings, cache):
    if "encrypt_options" not in settings:
        logging.error("Encrypt: no encrypt_options in settings")
        raise ValueError("no encrypt_options in settings")

    # try load credential from cache
    try:
        options = cache["credentials"]
    except KeyError:
        options = settings["encrypt_options"]

    table = str.maketrans({'"': r'\"', '\\': r'\\'})
    if "password" not in settings["encrypt_options"] \
            or len(settings["encrypt_options"]["password"]) == 0:
        logger.error("Encrypt: no password provided")
        raise ValueError("no password provided")
    else:
        options["password"] = settings["encrypt_options"]["password"]
        options["escaped_password"] = options["password"].translate(table)

    if "ask_password" not in options:
        options["ask_password"] = settings["encrypt_options"].get(
            "ask_password", False)
    options["filtered_password"] = "" if options["ask_password"] else options[
        "escaped_password"]

    if "gcm_tag" not in options:
        options["gcm_tag"] = gen_rand_string()
    options["escaped_gcm_tag"] = options["gcm_tag"].translate(table)

    if "kdf_salt" not in options:
        options["kdf_salt"] = gen_rand_string()
    options["escaped_kdf_salt"] = options["kdf_salt"].translate(table)

    if "galleryId" not in options:
        options["galleryId"] = gen_rand_string(6)

    if "kdf_iters" not in options:
        options["kdf_iters"] = 10000

    # in case any of the credentials are newly generated, write them back
    # to cache
    cache["credentials"] = {
        "gcm_tag": options["gcm_tag"],
        "kdf_salt": options["kdf_salt"],
        "kdf_iters": options["kdf_iters"],
        "galleryId": options["galleryId"]
    }

    return options


def cache_key(media):
    return os.path.join(media.path, media.dst_filename)


def save_property(cache, media):
    key = cache_key(media)
    if key not in cache:
        cache[key] = {}
        cache[key]["size"] = media.size
        cache[key]["thumb_size"] = media.thumb_size
        cache[key]["encrypted"] = set()


def get_encrypt_list(settings, media):
    to_encrypt = []
    # resized image or in case of "use_orig", the original
    to_encrypt.append(media.dst_filename)
    if settings["make_thumbs"]:
        to_encrypt.append(get_thumb(settings, media.dst_filename))  # thumbnail
    if media.big is not None and not settings["use_orig"]:
        to_encrypt.append(media.big)  # original image
    to_encrypt = list(
        map(lambda path: os.path.join(media.path, path), to_encrypt))
    return to_encrypt


def load_property(album):
    gallery = album.gallery
    cache = load_cache(gallery.settings)

    for media in album.medias:
        if media.type == "image":
            key = cache_key(media)
            if key in cache:
                media.size = cache[key]["size"]
                media.thumb_size = cache[key]["thumb_size"]


def load_cache(settings):
    cachePath = os.path.join(settings["destination"], ".encryptCache")
    try:
        with open(cachePath, "rb") as cacheFile:
            encryptCache = pickle.load(cacheFile)
            logger.debug("Loaded encryption cache with %d entries",
                         len(encryptCache))
            return encryptCache
    except FileNotFoundError:
        encryptCache = {}
        return encryptCache
    except Exception as e:
        logger.error("Could not load encryption cache: %s", e)
        logger.error("Giving up encryption. You may have to delete and "
                     "rebuild the entire gallery.")
        raise Abort


def save_cache(settings, cache):
    cachePath = os.path.join(settings["destination"], ".encryptCache")
    try:
        with open(cachePath, "wb") as cacheFile:
            pickle.dump(cache, cacheFile)
            logger.debug("Stored encryption cache with %d entries", len(cache))
    except Exception as e:
        logger.warning("Could not store encryption cache: %s", e)
        logger.warning("Next build of the gallery is likely to fail!")


def encrypt_gallery(gallery):
    albums = gallery.albums
    settings = gallery.settings

    cache = load_cache(settings)
    config = get_options(settings, cache)
    logger.debug("encryption config: %s", config)

    logger.info("starting encryption")
    copy_assets(settings)
    encrypt_files(settings, config, cache, albums, gallery.progressbar_target)
    save_cache(settings, cache)


def encrypt_files(settings, config, cache, albums, progressbar_target):
    if settings["keep_orig"] and settings["orig_link"]:
        logger.warning(
            "Original images are symlinked! Encryption is aborted. "
            "Please set 'orig_link' to False and restart gallery build.")
        raise Abort

    key = kdf_gen_key(config["password"], config["kdf_salt"],
                      config["kdf_iters"])
    gcm_tag = config["gcm_tag"].encode("utf-8")

    medias = list(chain.from_iterable(albums.values()))
    with progressbar(medias,
                     label="%16s" % "Encrypting files",
                     file=progressbar_target,
                     show_eta=True) as medias:
        for media in medias:
            if media.type != "image":
                logger.info("Skipping non-image file %s", media.src_filename)
                continue

            save_property(cache, media)
            to_encrypt = get_encrypt_list(settings, media)

            cacheEntry = cache[cache_key(media)]["encrypted"]
            for f in to_encrypt:
                if f in cacheEntry:
                    logger.info("Skipping %s as it is already encrypted", f)
                    continue

                full_path = os.path.join(settings["destination"], f)
                if encrypt_file(f, full_path, key, gcm_tag):
                    cacheEntry.add(f)
                else:
                    # save the progress and abort the build if any image
                    # fails to be encrypted
                    save_cache(settings, cache)
                    raise Abort

    key_check_path = os.path.join(settings["destination"], 'static',
                                  'keycheck.txt')
    encrypt_file("keycheck.txt", key_check_path, key, gcm_tag)


def encrypt_file(filename, full_path, key, gcm_tag):
    with BytesIO() as outBuffer:
        try:
            with open(full_path, "rb") as infile:
                encrypt(key, infile, outBuffer, gcm_tag)
        except Exception as e:
            logger.error("Encryption failed for %s: %s", filename, e)
            return False
        else:
            logger.info("Encrypting %s...", filename)
            try:
                with open(full_path, "wb") as outfile:
                    outfile.write(outBuffer.getbuffer())
            except Exception as e:
                logger.error("Could not write to file %s: %s", filename, e)
                return False
    return True


def copy_assets(settings):
    theme_path = os.path.join(settings["destination"], 'static')
    copy(os.path.join(ASSETS_PATH, "decrypt.js"),
         theme_path,
         symlink=False,
         rellink=False)
    copy(os.path.join(ASSETS_PATH, "keycheck.txt"),
         theme_path,
         symlink=False,
         rellink=False)
    copy(os.path.join(ASSETS_PATH, "sw.js"),
         settings["destination"],
         symlink=False,
         rellink=False)


def inject_scripts(context):
    cache = load_cache(context['settings'])
    context["encrypt_options"] = get_options(context['settings'], cache)


def register(settings):
    signals.gallery_build.connect(encrypt_gallery)
    signals.album_initialized.connect(load_property)
    signals.before_render.connect(inject_scripts)
