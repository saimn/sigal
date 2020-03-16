# Copyright 2019 - Remi Ferrand

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

""" This plugin controls the generation of a ZIP archive for a gallery

If the ``zip_gallery`` setting is set, it contains the location of a zip
archive with all original images of the corresponding directory.

To ignore a ZIP gallery generation for a particular album, put
a ``.nozip_gallery`` file next to it in its parent folder. Only the existence
of this ``.nozip_gallery`` file is tested.  If no ``.nozip_gallery`` file is
present, then make a ZIP archive with all media files.
"""

import logging
import os
import zipfile
from os.path import isfile, join, splitext

from sigal import signals
from sigal.gallery import Album
from sigal.utils import cached_property

logger = logging.getLogger(__name__)

def _should_generate_album_zip(album):
    """Checks whether a `.nozip_gallery` file exists in the album folder"""
    nozipgallerypath = os.path.join(album.src_path, ".nozip_gallery")
    return not os.path.isfile(nozipgallerypath)

def _generate_album_zip(album):
    """Make a ZIP archive with all media files and return its path.

    If the ``zip_gallery`` setting is set,it contains the location of a zip
    archive with all original images of the corresponding directory.
    """

    zip_gallery = album.settings['zip_gallery']

    if zip_gallery and len(album) > 0:
        zip_gallery = zip_gallery.format(album=album)
        archive_path = join(album.dst_path, zip_gallery)
        if (album.settings.get('zip_skip_if_exists', False) and
                isfile(archive_path)):
            logger.debug("Archive %s already created, passing", archive_path)
            return zip_gallery

        archive = zipfile.ZipFile(archive_path, 'w', allowZip64=True)
        attr = ('src_path' if album.settings['zip_media_format'] == 'orig'
                else 'dst_path')

        for p in album:
            path = getattr(p, attr)
            try:
                archive.write(path, os.path.split(path)[1])
            except OSError as e:
                logger.warn('Failed to add %s to the ZIP: %s', p, e)

        archive.close()
        logger.debug('Created ZIP archive %s', archive_path)
        return zip_gallery

    return False

def generate_album_zip(album):
    """Checks for .nozip_gallery file in album folder.
    If this file exists, no ZIP archive is generated.
    If the file is absent, make a ZIP archive with all media files and return its path.

    If the ``zip_gallery`` setting is set,it contains the location of a zip
    archive with all original images of the corresponding directory.
    """

    # check if ZIP file generation as been disabled by .nozip_gallery file
    if not _should_generate_album_zip(album):
        logger.info("Ignoring ZIP gallery generation for album '%s' because of present "
                    ".nozip_gallery file", album.name)
        return False

    return _generate_album_zip(album)

def nozip_gallery_file(album, settings=None):
    """Filesystem based switch to disable ZIP generation for an Album"""
    Album.zip = cached_property(generate_album_zip)

def register(settings):
    signals.album_initialized.connect(nozip_gallery_file)
