"""Plugin to index non-media files.

This plugin will copy the files into the build tree and generate generic
thumbnails for the files.  In-browser previews will likely fail, and
it is up to the theme to provide correct support for downloads.

Settings available as dictionary in ``nonmedia_files_options``:

- ``ext_as_thumb``: Enable simple thumbnail showing ext.
  Default to ``True``
- ``ignore_ext``: List of file extensions to ignore.
  Default to ``[".md"]``

"""

import logging
import os

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

from pilkit.utils import save_image

from sigal import signals
from sigal import utils
from sigal.gallery import Media
from sigal.settings import Status

logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    'ext_as_thumb': True,
    'ignore_ext': ['.md'],
}


COMMON_MIME_TYPES = {
    '.azw': 'application/vnd.amazon.ebook',
    '.csv': 'text/csv',
    '.epub': 'application/epub+zip',
    '.pdf': 'application/pdf',
    '.svg': 'image/svg+xml',
    '.txt': 'text/plain',
    '.zip': 'application/zip',
}


def get_mime(ext):
    if ext in COMMON_MIME_TYPES:
        return COMMON_MIME_TYPES[ext]
    return 'application/octet-stream'


class NonMedia(Media):
    """Gather all informations on a non-media file."""

    type = 'nonmedia'

    def __init__(self, filename, path, settings):
        super().__init__(filename, path, settings)
        self.thumb_name = os.path.splitext(self.thumb_name)[0] + '.jpg'
        self.date = self._get_file_date()
        self.mime = get_mime(self.src_ext)
        logger.debug('mime type %s', self.mime)

    @property
    def thumbnail(self):
        """Path to the thumbnail image (relative to the album directory)."""
        if not os.path.isfile(self.thumb_path):
            generate_thumbnail(self.src_ext[1:].upper(), self.thumb_path,
                               self.settings['thumb_size'])
        return super().thumbnail


def generate_thumbnail(text, outname, box, options=None):
    """Create a thumbnail image."""
    img = PILImage.new("RGB", box, (255, 255, 255))

    fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 40)
    anchor = (box[0] // 2, box[1] // 2)
    d = ImageDraw.Draw(img)
    d.text(anchor, text, font=fnt, fill=(0, 0, 0), anchor='mm')

    outformat = 'JPEG'
    logger.info('Save thumnail image: %s (%s)', outname, outformat)
    save_image(img, outname, outformat, options=options, autoconvert=True)


def process_nonmedia(media):
    """Process a non-media file: copy and create thumbnail."""
    logger.info('Processing non-media file: %s', media.dst_filename)
    settings = media.settings
    plugin_settings = settings.get('nonmedia_files_settings', {})

    try:
        utils.copy(media.src_path, media.dst_path,
                   symlink=settings['orig_link'])
    except Exception:
        if logger.getEffectiveLevel() == logging.DEBUG:
            raise
        else:
            return Status.FAILURE

    if plugin_settings.get('ext_as_thumb', DEFAULT_CONFIG['ext_as_thumb']):
        try:
            generate_thumbnail(
                media.src_ext[1:].upper(),
                media.thumb_path,
                settings['thumb_size'],
                options=settings['jpg_options'],
            )
        except Exception:
            if logger.getEffectiveLevel() == logging.DEBUG:
                raise
            else:
                return Status.FAILURE


def album_file(album, filename, media=None):
    if not media:
        ext = os.path.splitext(filename)[1]
        ext_ignore = album.settings.get('nonmedia_files_settings', {}).get(
            'ignore_ext', DEFAULT_CONFIG['ignore_ext'])
        if ext in ext_ignore:
            logger.info('Ignoring non-media file: %s', filename)
        else:
            logger.info('Registering non-media file: %s', filename)
            return NonMedia(filename, album.path, album.settings)


def process_file(media, processor=None):
    if media.type == 'nonmedia':
        return process_nonmedia


def register(settings):
    signals.album_file.connect(album_file)
    signals.process_file.connect(process_file)
