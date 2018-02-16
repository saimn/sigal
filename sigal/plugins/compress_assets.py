"""Plugin to compress static files for faster HTTP transfer.

Your web server must be configured in order to select pre-compressed
files instead of the required one, to save CPU. For example, in nginx::

    server {
        gzip_static;
    }

Currently, 3 methods are supported:

- ``gzip``: No dependency required.
  This is the fastest, but also largest output.
- ``zopfli``: Requires zopfli_.
  gzip compatible output with optimized size.
- ``brotli``: Requires brotli_.
  Brotli is the best compressor for web usage.

.. _zopfli: https://pypi.python.org/pypi/zopfli
.. _brotli: https://pypi.python.org/pypi/Brotli

Settings available as dictionary in ``compress_assets_options``:

- ``method``: One of ``gzip``, ``zopfli`` or ``brotli``.
- ``suffixes``: List of file suffixes eligible to compression.
  Default to ``['htm', 'html', 'css', 'js', 'svg']``

"""

import logging
import gzip
import shutil
import os

from sigal import signals
from click import progressbar

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
        'suffixes': ['htm', 'html', 'css', 'js', 'svg'],
        'method': 'gzip',
        }


class BaseCompressor:
    suffix = None

    def __init__(self, settings):
        self.suffixes_to_compress = settings.get('suffixes', DEFAULT_SETTINGS['suffixes'])

    def do_compress(self, filename, compressed_filename):
        '''
        Perform actual compression.
        This should be implemented by subclasses.
        '''
        raise NotImplementedError

    def compress(self, filename):
        '''
        Compress a file, only if needed.
        '''
        compressed_filename = self.get_compressed_filename(filename)
        if not compressed_filename:
            return

        self.do_compress(filename, compressed_filename)

    def get_compressed_filename(self, filename):
        '''
        If the given filename should be compressed, returns the compressed filename.
        A file can be compressed if:
            - It is a whitelisted extension
            - The compressed file does not exist
            - The compressed file exists by is older than the file itself
        Otherwise, it returns False.
        '''
        if not os.path.splitext(filename)[1][1:] in self.suffixes_to_compress:
            return False

        file_stats = None
        compressed_stats = None
        compressed_filename = u'{}.{}'.format(filename, self.suffix)
        try:
            file_stats = os.stat(filename)
            compressed_stats = os.stat(compressed_filename)
        except OSError:  # FileNotFoundError is for Python3 only
            pass

        if file_stats and compressed_stats:
            return compressed_filename if file_stats.st_mtime > compressed_stats.st_mtime else False
        else:
            return compressed_filename


class GZipCompressor(BaseCompressor):
    suffix = 'gz'

    def do_compress(self, filename, compressed_filename):
        with open(filename, 'rb') as f_in, gzip.open(compressed_filename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


class ZopfliCompressor(BaseCompressor):
    suffix = 'gz'

    def do_compress(self, filename, compressed_filename):
        import zopfli.gzip
        with open(filename, 'rb') as f_in, open(compressed_filename, 'wb') as f_out:
            f_out.write(zopfli.gzip.compress(f_in.read()))


class BrotliCompressor(BaseCompressor):
    suffix = 'br'

    def do_compress(self, filename, compressed_filename):
        import brotli
        with open(filename, 'rb') as f_in, open(compressed_filename, 'wb') as f_out:
            f_out.write(brotli.compress(f_in.read(), mode=brotli.MODE_TEXT))


def get_compressor(settings):
    name = settings.get('method', DEFAULT_SETTINGS['method'])
    if name == 'gzip':
        return GZipCompressor(settings)
    elif name == 'zopfli':
        try:
            import zopfli.gzip
            return ZopfliCompressor(settings)
        except ImportError:
            logging.error('Unable to import zopfli module')

    elif name == 'brotli':
        try:
            import brotli
            return BrotliCompressor(settings)
        except ImportError:
            logger.error('Unable to import brotli module')

    else:
        logger.error('No such compressor {}'.format(name))


def compress_gallery(gallery):
    logging.info('Compressing assets for %s', gallery.title)
    compress_settings = gallery.settings.get('compress_assets_options', DEFAULT_SETTINGS)
    compressor = get_compressor(compress_settings)

    if compressor is None:
        return

    # Collecting theme assets
    theme_assets = []
    for current_directory, _, filenames in os.walk(os.path.join(gallery.settings['destination'], 'static')):
        for filename in filenames:
            theme_assets.append(os.path.join(current_directory, filename))

    with progressbar(length=len(gallery.albums) + len(theme_assets), label='Compressing static files') as bar:
        for album in gallery.albums.values():
            compressor.compress(os.path.join(album.dst_path, album.output_file))
            bar.update(1)

        for theme_asset in theme_assets:
            compressor.compress(theme_asset)
            bar.update(1)


def register(settings):
    if settings['write_html']:
        signals.gallery_build.connect(compress_gallery)
