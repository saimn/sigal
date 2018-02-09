# -*- coding:utf-8 -*-

import os

import pytest

from sigal.gallery import Gallery
from sigal import init_plugins
from sigal.plugins import compress_assets


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


def _test_compress_generic(settings, tmpdir, method, compress_suffix, test_import=None):
    if test_import:
        pytest.importorskip(test_import)
    compress_options = make_gallery(settings, tmpdir, 'gzip')

    suffixes = compress_options['suffixes']

    for path, dirs, files in os.walk(settings['destination']):
        for file in files:
            path_exists = os.path.exists('{}.{}'.format(os.path.join(path, file), 'gz'))
            file_ext = os.path.splitext(file)[1][1:]
            assert path_exists if file_ext in suffixes else not path_exists


def test_compress_gzip(settings, tmpdir):
    _test_compress_generic(settings, tmpdir, 'gzip', 'gz')


def test_compress_zopfli(settings, tmpdir):
    _test_compress_generic(settings, tmpdir, 'zopfli', 'gz', 'zopfli.gzip')


def test_compress_brotli(settings, tmpdir):
    _test_compress_generic(settings, tmpdir, 'brotli', 'br', 'brotli')
