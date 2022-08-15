import os
import pickle
from io import BytesIO

import pytest

from sigal import init_plugins
from sigal.gallery import Gallery
from sigal.plugins.encrypt import endec
from sigal.plugins.encrypt.encrypt import cache_key

CURRENT_DIR = os.path.dirname(__file__)


def get_key_tag(settings):
    options = settings["encrypt_options"]
    key = endec.kdf_gen_key(
        options["password"], options["kdf_salt"], options["kdf_iters"]
    )
    tag = options["gcm_tag"].encode("utf-8")
    return (key, tag)


def test_encrypt(settings, tmpdir, disconnect_signals, caplog):
    settings['destination'] = str(tmpdir)
    if "sigal.plugins.encrypt" not in settings["plugins"]:
        settings['plugins'] += ["sigal.plugins.encrypt"]

    init_plugins(settings)
    gal = Gallery(settings)

    with pytest.raises(ValueError, match="no encrypt_options in settings"):
        gal.build()

    settings['encrypt_options'] = {}

    gal = Gallery(settings)

    with pytest.raises(ValueError, match="no password provided"):
        gal.build()

    settings['encrypt_options'] = {
        'password': 'password',
        'ask_password': True,
        'encrypt_symlinked_originals': False,
    }

    gal = Gallery(settings)
    gal.build()

    # check the encrypt cache exists
    cachePath = os.path.join(settings["destination"], ".encryptCache")
    assert os.path.isfile(cachePath)

    encryptCache = None
    with open(cachePath, "rb") as cacheFile:
        encryptCache = pickle.load(cacheFile)
    assert isinstance(encryptCache, dict)

    testAlbum = gal.albums["encryptTest"]
    key, tag = get_key_tag(settings)

    for media in testAlbum:
        # check if sizes are stored in cache
        assert cache_key(media) in encryptCache
        assert "size" in encryptCache[cache_key(media)]
        assert "thumb_size" in encryptCache[cache_key(media)]
        assert "encrypted" in encryptCache[cache_key(media)]

        encryptedImages = [media.dst_path, media.thumb_path]
        if settings["keep_orig"]:
            encryptedImages.append(
                os.path.join(settings["destination"], media.path, media.big)
            )

        # check if images are encrypted by trying to decrypt
        for image in encryptedImages:
            with open(image, "rb") as infile:
                with BytesIO() as outfile:
                    endec.decrypt(key, infile, outfile, tag)

    # check static files have been copied
    static = os.path.join(settings["destination"], 'static')
    assert os.path.isfile(os.path.join(static, "decrypt.js"))
    assert os.path.isfile(os.path.join(static, "keycheck.txt"))
    assert os.path.isfile(os.path.join(settings["destination"], "sw.js"))

    # check keycheck file
    with open(
        os.path.join(settings["destination"], 'static', "keycheck.txt"), "rb"
    ) as infile:
        with BytesIO() as outfile:
            endec.decrypt(key, infile, outfile, tag)

    caplog.clear()
    caplog.set_level('DEBUG')
    gal = Gallery(settings)
    gal.build()
    # Doesn't work on Actions ...
    # assert 'Loaded cache with 34 entries' in caplog.messages
    # assert 'Loaded encryption cache with 27 entries' in caplog.messages
