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

'''Plugin to protect gallery by encrypting image files using a password.

Options::

    encrypt_options = {
        'password': 'password',
        'ask_password': False,
        'gcm_tag': 'randomly_generated',
        'kdf_salt': 'randomly_generated',
        'kdf_iters': 10000,
        'encrypt_symlinked_originals': False
    }

- ``password``: The password used to encrypt the images on gallery build, 
  and decrypt them when viewers access the gallery. No default value. You must
  specify a password.
- ``ask_password``: Whether or not viewers are asked for the password to view 
  the gallery. If set to ``False``, the password will be present in the HTML files
  so the images are decrypted automatically. Defaults to ``False``.
- ``gcm_tag``, ``kdf_salt``, ``kdf_iters``: Cryptographic parameters used when
  encrypting the files. ``gcm_tag``, ``kdf_salt`` are meant to be randomly generated, 
  ``kdf_iters`` defaults to 10000. Do not specify them in the config file unless 
  you have good reasons to do so.
- ``encrypt_symlinked_originals``: Force encrypting original images even if they 
  are symlinked. If you don't know what it means, leave it to ``False``.

Note: The plugin caches the cryptographic parameters (but not the password) after 
the first build, so that incremental builds can share the same credentials. 
DO NOT CHANGE THE PASSWORD OR OTHER CRYPTOGRAPHIC PARAMETERS ONCE A GALLERY IS 
BUILT, or there will be inconsistency in encrypted files and viewers will not be able
to see some of the images any more.
'''

import os
import random
import string
import logging
import pickle
from io import BytesIO
from itertools import chain

from sigal import signals
from sigal.utils import url_from_path, copy
from sigal.settings import get_thumb
from click import progressbar

from .endec import encrypt, kdf_gen_key

logger = logging.getLogger(__name__)

ASSETS_PATH = os.path.normpath(os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'static'))

class Abort(Exception):
    pass

def gen_rand_string(length=16):
    return "".join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=length))

def get_options(settings, cache):
    if "encrypt_options" not in settings:
        logging.error("Encrypt: no options in settings")
        raise Abort
    
    # try load credential from cache
    try:
        options = cache["credentials"]
    except KeyError:
        options = settings["encrypt_options"]

    table = str.maketrans({'"': r'\"', '\\': r'\\'})
    if "password" not in settings["encrypt_options"] \
        or len(settings["encrypt_options"]["password"]) == 0:
        logger.error("Encrypt: no password provided")
        raise Abort
    else:
        options["password"] = settings["encrypt_options"]["password"]
        options["escaped_password"] = options["password"].translate(table)

    if "ask_password" not in options:
        options["ask_password"] = settings["encrypt_options"].get("ask_password", False)
    options["filtered_password"] = "" if options["ask_password"] else options["escaped_password"]

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

    # in case any of the credentials are newly generated, write them back to cache
    cache["credentials"] = {
        "gcm_tag": options["gcm_tag"],
        "kdf_salt": options["kdf_salt"],
        "kdf_iters": options["kdf_iters"],
        "galleryId": options["galleryId"]
    }

    if "encrypt_symlinked_originals" not in options:
        options["encrypt_symlinked_originals"] = settings["encrypt_options"].get("encrypt_symlinked_originals", False)

    return options

def cache_key(media):
    return os.path.join(media.path, media.filename)

def save_property(cache, media):
    key = cache_key(media)
    if key not in cache:
        cache[key] = {}
        cache[key]["size"] = media.size
        cache[key]["thumb_size"] = media.thumb_size
        cache[key]["encrypted"] = set()

def get_encrypt_list(settings, media):
    to_encrypt = []
    to_encrypt.append(media.filename) #resized image
    if settings["make_thumbs"]:
        to_encrypt.append(get_thumb(settings, media.filename)) #thumbnail
    if media.big is not None:
        to_encrypt.append(media.big) #original image
    to_encrypt = list(map(lambda path: os.path.join(media.path, path), to_encrypt))
    return to_encrypt

def load_property(album):
    gallery = album.gallery
    try:
        cache = load_cache(gallery.settings)
    except Abort:
        return

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
            logger.debug("Loaded encryption cache with %d entries", len(encryptCache))
            return encryptCache
    except FileNotFoundError:
        encryptCache = {}
        return encryptCache
    except Exception as e:
        logger.error("Could not load encryption cache: %s", e)
        logger.error("Giving up encryption. Please delete and rebuild the entire gallery.")
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
    
    try:
        cache = load_cache(settings)
        config = get_options(settings, cache)
        logger.debug("encryption config: %s", config)
        # make cache available from gallery object
        # gallery.encryptCache = cache

        logger.info("starting encryption")
        copy_assets(settings)
        encrypt_files(settings, config, cache, albums, gallery.progressbar_target)
        save_cache(settings, cache)
    except Abort:
        pass

def encrypt_files(settings, config, cache, albums, progressbar_target):
    if settings["keep_orig"]:
        if settings["orig_link"] and not config["encrypt_symlinked_originals"]:
            logger.warning("Original files are symlinked! Set encrypt_options[\"encrypt_symlinked_originals\"] to True to force encrypting them, if this is what you want.")
            raise Abort

    key = kdf_gen_key(config["password"], config["kdf_salt"], config["kdf_iters"])
    gcm_tag = config["gcm_tag"].encode("utf-8")

    medias = list(chain.from_iterable(albums.values()))
    with progressbar(medias, label="%16s" % "Encrypting files", file=progressbar_target, show_eta=True) as medias:
        for media in medias:
            if media.type != "image":
                logger.info("Skipping non-image file %s", media.filename)
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

    key_check_path = os.path.join(settings["destination"], 'static', 'keycheck.txt')
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
    copy(os.path.join(ASSETS_PATH, "decrypt.js"), theme_path, symlink=False, rellink=False)
    copy(os.path.join(ASSETS_PATH, "keycheck.txt"), theme_path, symlink=False, rellink=False)
    copy(os.path.join(ASSETS_PATH, "sw.js"), settings["destination"], symlink=False, rellink=False)

def inject_scripts(context):
    try:
        cache = load_cache(context['settings'])
        context["encrypt_options"] = get_options(context['settings'], cache)
    except Abort:
        # we can't do anything useful without info in cache
        # so just return the context unmodified
        pass
    
    return context

def register(settings):
    signals.gallery_build.connect(encrypt_gallery)
    signals.album_initialized.connect(load_property)
    signals.before_render.connect(inject_scripts)

