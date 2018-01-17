#!/usr/bin/env python3

"""Plugin to compress static files for faster HTTP transfer.

Currently, 3 methods are supported:
    - gzip. No dependency required. This is the fastest, but also largest output.
    - zopfli. Need zopfli module from https://pypi.python.org/pypi/zopfli. gzip compatible output with optimized size.
    - brotli. Need brotli module from https://pypi.python.org/pypi/Brotli. Brotli is the best compressor for web usage.

"""
import logging
import gzip
import shutil
import os
import os.path

from pathlib import Path

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

    def compressed_filename(self, filename):
        suffix = self.suffix()
        return filename.with_name(f'{filename.name}.{suffix}')

    def suffix(self):
        raise NotImplementedError

    def do_compress(self, filename, compressed_filename):
        raise NotImplementedError

    def compress_file(self, filename):
        compressed_filename = self.can_compress(filename)
        if not compressed_filename:
            return

        self.do_compress(filename, compressed_filename)

    def can_compress(self, filename):
        # Be sure it's a path
        filename = Path(filename)
        if not filename.suffix[1:] in self.settings['suffixes']:
            return False

        file_stats = None
        compressed_stats = None
        compressed_filename_result = self.compressed_filename(filename)
        try:
            file_stats = os.stat(filename)
            compressed_stats = os.stat(compressed_filename_result)
        except FileNotFoundError:
            pass

        if file_stats and compressed_stats:
            return compressed_filename_result if file_stats.st_mtime > compressed_stats.st_mtime else False
        else:
            return compressed_filename_result


class GZipCompressor(BaseCompressor):

    def suffix(self):
        return 'gz'

    def do_compress(self, filename, compressed_filename):
        with open(filename, 'rb') as f_in, gzip.open(compressed_filename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


class ZopfliCompressor(BaseCompressor):

    def suffix(self):
        return 'gz'

    def do_compress(self, filename, compressed_filename):
        with open(filename, 'rb') as f_in, open(compressed_filename, 'wb') as f_out:
            f_out.write(zopfli.gzip.compress(f_in.read()))


class BrotliCompressor(BaseCompressor):

    def suffix(self):
        return 'br'

    def do_compress(self, filename, compressed_filename):
        with open(filename, 'rb') as f_in, open(compressed_filename, 'wb') as f_out:
            f_out.write(brotli.compress(f_in.read(), mode=brotli.MODE_TEXT))


def get_compressor(settings):
    name = settings.get('method', '')
    if name == 'gzip':
        return GZipCompressor(settings)
    elif name == 'zopfli':
        try:
            global zopfli
            import zopfli.gzip
            return ZopfliCompressor(settings)
        except ImportError:
            logging.warning('Zopfli not found, using standard gzip')
            return GZipCompressor(settings)

    elif name == 'brotli':
        try:
            global brotli
            import brotli
            return BrotliCompressor(settings)
        except ImportError:
            logger.error('Unable to import brotli module')

    else:
        logger.error(f'No such compressor {name}')


def compress_assets(assets_directory, compressor):
    assets = []
    for current_directory, _, filenames in os.walk(assets_directory):
        for filename in filenames:
            assets.append(os.path.join(current_directory, filename))

    with progressbar(assets, label='Compressing theme assets') as progress_compress:
        for filename in progress_compress:
            compressor.compress_file(filename)


def compress_gallery(gallery):
    logging.info(f'Compressing assets for {gallery.title}')
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
