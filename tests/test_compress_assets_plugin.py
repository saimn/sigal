# -*- coding:utf-8 -*-

import os
import pytest

from sigal import init_plugins
from sigal.gallery import Gallery
from sigal.plugins import compress_assets

CURRENT_DIR = os.path.dirname(__file__)


def make_gallery(settings, tmpdir, method):
    settings['destination'] = str(tmpdir)
    if "sigal.plugins.compress_assets" not in settings["plugins"]:
        settings['plugins'] += ["sigal.plugins.compress_assets"]

    # Set method
    settings.setdefault('compress_assets_options', {})['method'] = method

    compress_options = compress_assets.DEFAULT_SETTINGS.copy()
    # The key was created by the previous setdefault if needed
    compress_options.update(settings['compress_assets_options'])

    init_plugins(settings)
    gal = Gallery(settings)
    gal.build()

    return compress_options


@pytest.mark.parametrize("method,compress_suffix,test_import",
                         [('gzip', 'gz', None),
                          ('zopfli', 'gz', 'zopfli.gzip'),
                          ('brotli', 'br', 'brotli')])
def test_compress(disconnect_signals, settings, tmpdir, method,
                  compress_suffix, test_import):
    if test_import:
        pytest.importorskip(test_import)
    compress_options = make_gallery(settings, tmpdir, method)

    suffixes = compress_options['suffixes']

    for path, dirs, files in os.walk(settings['destination']):
        for file in files:
            path_exists = os.path.exists('{}.{}'.format(os.path.join(path, file), compress_suffix))
            file_ext = os.path.splitext(file)[1][1:]
            assert path_exists if file_ext in suffixes else not path_exists
