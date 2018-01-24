#!/usr/bin/env python3

"""Plugin to compress static files for faster HTTP transfer.

Currently, 3 methods are supported:
    - gzip. No dependency required. This is the fastest, but also largest output.
    - zopfli. Need zopfli module from https://pypi.python.org/pypi/zopfli. gzip compatible output with optimized size.
    - brotli. Need brotli module from https://pypi.python.org/pypi/Brotli. Brotli is the best compressor for web usage.

"""

from __future__ import unicode_literals

import logging
import gzip
import shutil
import os

from sigal import signals
from click import progressbar

logger = logging.getLogger(__name__)

SETTINGS = {
        'suffixes': ['htm', 'html', 'css', 'js', 'svg'],
        'method': 'gzip',
        }


class BaseCompressor:

    def __init__(self, settings):
        self.settings = settings
        self.suffix = self.__class__.SUFFIX

    def compressed_filename(self, filename):
        return '{}.{}'.format(filename, self.suffix)

    def do_compress(self, filename, compressed_filename):
        raise NotImplementedError

    def compress_file(self, filename):
        compressed_filename = self.can_compress(filename)
        if not compressed_filename:
            return

        self.do_compress(filename, compressed_filename)

    def can_compress(self, filename):
        if not os.path.splitext(filename)[1][1:] in self.settings['suffixes']:
            return False

        file_stats = None
        compressed_stats = None
        compressed_filename_result = self.compressed_filename(filename)
        try:
            file_stats = os.stat(filename)
            compressed_stats = os.stat(compressed_filename_result)
        except OSError: # FileNotFoundError is for Python3 only
            pass

        if file_stats and compressed_stats:
            return compressed_filename_result if file_stats.st_mtime > compressed_stats.st_mtime else False
        else:
            return compressed_filename_result


class GZipCompressor(BaseCompressor):
    SUFFIX = 'gz'

    def do_compress(self, filename, compressed_filename):
        with open(filename, 'rb') as f_in, gzip.open(compressed_filename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


class ZopfliCompressor(BaseCompressor):
    SUFFIX = 'gz'

    def do_compress(self, filename, compressed_filename):
        import zopfli.gzip
        with open(filename, 'rb') as f_in, open(compressed_filename, 'wb') as f_out:
            f_out.write(zopfli.gzip.compress(f_in.read()))


class BrotliCompressor(BaseCompressor):
    SUFFIX = 'br'

    def do_compress(self, filename, compressed_filename):
        import brotli
        with open(filename, 'rb') as f_in, open(compressed_filename, 'wb') as f_out:
            f_out.write(brotli.compress(f_in.read(), mode=brotli.MODE_TEXT))


def get_compressor(settings):
    name = settings.get('method', '')
    if name == 'gzip':
        return GZipCompressor(settings)
    elif name == 'zopfli':
        try:
            import zopfli.gzip
            return ZopfliCompressor(settings)
        except ImportError:
            logging.warning('Zopfli not found, using standard gzip')
            return GZipCompressor(settings)

    elif name == 'brotli':
        try:
            import brotli
            return BrotliCompressor(settings)
        except ImportError:
            logger.error('Unable to import brotli module')

    else:
        logger.error('No such compressor {}'.format(name))


def compress_assets(assets_directory, compressor):
    assets = []
    for current_directory, _, filenames in os.walk(assets_directory):
        for filename in filenames:
            assets.append(os.path.join(current_directory, filename))

    with progressbar(assets, label='Compressing theme assets') as progress_compress:
        for filename in progress_compress:
            compressor.compress_file(filename)


def compress_gallery(gallery):
    logging.info('Compressing assets for {}'.format(gallery.title))
    settings = SETTINGS.copy()
    settings.update(gallery.settings.get('compress_assets_options', {}))
    compressor = get_compressor(settings)

    if compressor is None:
        return

    with progressbar(gallery.albums.values(), label='Compressing albums static files') as progress_compress:
        for album in progress_compress:
            compressor.compress_file(os.path.join(album.dst_path, album.output_file))

    compress_assets(os.path.join(gallery.settings['destination'], 'static'), compressor)


def register(settings):
    if settings['write_html']:
        signals.gallery_build.connect(compress_gallery)
