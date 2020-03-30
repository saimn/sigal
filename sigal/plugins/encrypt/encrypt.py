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

Options:
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

import os, random, string, logging, pickle
from io import BytesIO
from itertools import chain

from sigal import signals
from sigal.utils import url_from_path, copy
from sigal.settings import get_thumb
from click import progressbar
from bs4 import BeautifulSoup

from .endec import encrypt, kdf_gen_key

ASSETS_PATH = os.path.normpath(os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'static'))

class Abort(Exception):
    pass

def gen_rand_string(length=16):
    return "".join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=length))

def get_options(gallery):
    settings = gallery.settings
    cache = gallery.encryptCache
    if "encrypt_options" not in settings:
        raise ValueError("Encrypt: no options in settings")
    
    #try load credential from cache
    try:
        options = cache["credentials"]
    except KeyError:
        options = settings["encrypt_options"]

    table = str.maketrans({'"': r'\"', '\\': r'\\'})
    if "password" not in settings["encrypt_options"]:
        raise ValueError("Encrypt: no password provided")
    else:
        options["password"] = settings["encrypt_options"]["password"]
        options["escaped_password"] = options["password"].translate(table)

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

    if "ask_password" not in options:
        options["ask_password"] = settings["encrypt_options"].get("ask_password", False)

    gallery.encryptCache["credentials"] = {
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
    if not hasattr(album.gallery, "encryptCache"):
        load_cache(album.gallery)
    cache = album.gallery.encryptCache

    for media in album.medias:
        if media.type == "image":
            key = cache_key(media)
            if key in cache:
                media.size = cache[key]["size"]
                media.thumb_size = cache[key]["thumb_size"]

def load_cache(gallery):
    if hasattr(gallery, "encryptCache"):
        return
    logger = gallery.logger
    settings = gallery.settings
    cachePath = os.path.join(settings["destination"], ".encryptCache")

    try:
        with open(cachePath, "rb") as cacheFile:
            gallery.encryptCache = pickle.load(cacheFile)
            logger.debug("Loaded encryption cache with %d entries", len(gallery.encryptCache))
    except FileNotFoundError:
        gallery.encryptCache = {}
    except Exception as e:
        logger.error("Could not load encryption cache: %s", e)
        logger.error("Giving up encryption. Please delete and rebuild the entire gallery.")
        raise Abort

def save_cache(gallery):
    if hasattr(gallery, "encryptCache"):
        cache = gallery.encryptCache
    else:
        cache = gallery.encryptCache = {}
    
    logger = gallery.logger
    settings = gallery.settings
    cachePath = os.path.join(settings["destination"], ".encryptCache")
    try:
        with open(cachePath, "wb") as cacheFile:
            pickle.dump(cache, cacheFile)
            logger.debug("Stored encryption cache with %d entries", len(cache))
    except Exception as e:
        logger.warning("Could not store encryption cache: %s", e)
        logger.warning("Next build of the gallery is likely to fail!")

def encrypt_gallery(gallery):
    logger = gallery.logger
    albums = gallery.albums
    settings = gallery.settings
    
    try:
        load_cache(gallery)
        config = get_options(gallery)
        logger.debug("encryption config: %s", config)
        logger.info("starting encryption")
        encrypt_files(gallery, settings, config, albums)
        fix_html(gallery, settings, config, albums)
        copy_assets(settings)
    except Abort:
        pass

    save_cache(gallery)

def encrypt_files(gallery, settings, config, albums):
    logger = gallery.logger
    if settings["keep_orig"]:
        if settings["orig_link"] and not config["encrypt_symlinked_originals"]:
            logger.warning("Original files are symlinked! Set encrypt_options[\"encrypt_symlinked_originals\"] to True to force encrypting them, if this is what you want.")
            raise Abort

    key = kdf_gen_key(config["password"].encode("utf-8"), config["kdf_salt"].encode("utf-8"), config["kdf_iters"])
    medias = list(chain.from_iterable(albums.values()))
    with progressbar(medias, label="%16s" % "Encrypting files", file=gallery.progressbar_target, show_eta=True) as medias:
        for media in medias:
            if media.type != "image":
                logger.info("Skipping non-image file %s", media.filename)
                continue

            save_property(gallery.encryptCache, media)
            to_encrypt = get_encrypt_list(settings, media)

            cacheEntry = gallery.encryptCache[cache_key(media)]["encrypted"]
            for f in to_encrypt:
                if f in cacheEntry:
                    logger.info("Skipping %s as it is already encrypted", f)
                    continue

                full_path = os.path.join(settings["destination"], f)
                with BytesIO() as outBuffer:
                    try:
                        with open(full_path, "rb") as infile:
                            encrypt(key, infile, outBuffer, config["gcm_tag"].encode("utf-8"))
                    except Exception as e:
                        logger.error("Encryption failed for %s: %s", f, e)
                    else:
                        logger.info("Encrypting %s...", f)
                        try:
                            with open(full_path, "wb") as outfile:
                                outfile.write(outBuffer.getbuffer())
                            cacheEntry.add(f)
                        except Exception as e:
                            logger.error("Could not write to file %s: %s", f, e)

def fix_html(gallery, settings, config, albums):
    logger = gallery.logger
    if gallery.settings["write_html"]:
        decryptorConfigTemplate = """
        Decryptor.init({{
            password: "{filtered_password}",
            worker_script: "{worker_script}",
            galleryId: "{galleryId}",
            gcm_tag: "{escaped_gcm_tag}", 
            kdf_salt: "{escaped_kdf_salt}", 
            kdf_iters: {kdf_iters} 
        }});
        """
        config["filtered_password"] = "" if config.get("ask_password", False) else config["escaped_password"]

        with progressbar(albums.values(), label="%16s" % "Fixing html files", file=gallery.progressbar_target, show_eta=True) as albums:
            for album in albums:
                index_file = os.path.join(album.dst_path, album.output_file)
                contents = None
                with open(index_file, "r", encoding="utf-8") as f:
                    contents = f.read()
                root = BeautifulSoup(contents, "html.parser")
                head = root.find("head")
                if head.find(id="_decrypt_script"):
                    head.find(id="_decrypt_script").decompose()
                if head.find(id="_decrypt_script_config"):
                    head.find(id="_decrypt_script_config").decompose()
                theme_path = os.path.join(settings["destination"], 'static')
                theme_url = url_from_path(os.path.relpath(theme_path, album.dst_path))
                scriptNode = root.new_tag("script", id="_decrypt_script", src="{url}/decrypt.js".format(url=theme_url))
                scriptConfig = root.new_tag("script", id="_decrypt_script_config")
                config["worker_script"] = "{url}/decrypt-worker.js".format(url=theme_url)
                decryptorConfig = decryptorConfigTemplate.format(**config)
                scriptConfig.append(root.new_string(decryptorConfig))
                head.append(scriptNode)
                head.append(scriptConfig)
                with open(index_file, "w", encoding="utf-8") as f:
                    f.write(root.prettify())

def copy_assets(settings):
    theme_path = os.path.join(settings["destination"], 'static')
    for root, dirs, files in os.walk(ASSETS_PATH):
        for file in files:
            copy(os.path.join(root, file), theme_path, symlink=False, rellink=False)


def register(settings):
    signals.gallery_build.connect(encrypt_gallery)
    signals.album_initialized.connect(load_property)

