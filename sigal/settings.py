# -*- coding:utf-8 -*-

# Copyright (c) 2009-2014 - Simon Conseil
# Copyright (c) 2013      - Christophe-Marie Duquesne

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

import locale
import logging
import os
from os.path import abspath, isabs, join, normpath
from pprint import pformat

from .compat import PY2


_DEFAULT_CONFIG = {
    'albums_sort_reverse': False,
    'autorotate_images': True,
    'colorbox_column_size': 4,
    'copy_exif_data': False,
    'destination': '_build',
    'files_to_copy': (),
    'google_analytics': '',
    'ignore_directories': [],
    'ignore_files': [],
    'img_processor': 'ResizeToFit',
    'img_size': (640, 480),
    'index_in_url': False,
    'jpg_options': {'quality': 85, 'optimize': True, 'progressive': True},
    'keep_orig': False,
    'links': '',
    'locale': '',
    'medias_sort_attr': 'filename',
    'medias_sort_reverse': False,
    'make_thumbs': True,
    'output_filename': 'index.html',
    'orig_dir': 'original',
    'orig_link': False,
    'plugins': [],
    'plugin_paths': [],
    'source': '',
    'theme': 'colorbox',
    'thumb_dir': 'thumbnails',
    'thumb_fit': True,
    'thumb_prefix': '',
    'thumb_size': (200, 150),
    'thumb_suffix': '',
    'title': '',
    'video_size': (480, 360),
    'webm_options': ['-crf', '10', '-b:v', '1.6M',
                     '-qmin', '4', '-qmax', '63'],
    'write_html': True,
    'zip_gallery': False,
    'zip_media_format': 'resized',
}


def get_thumb(settings, filename):
    """Return the path to the thumb.

    examples:
    >>> default_settings = create_settings()
    >>> get_thumb(default_settings, "bar/foo.jpg")
    "bar/thumbnails/foo.jpg"
    >>> get_thumb(default_settings, "bar/foo.png")
    "bar/thumbnails/foo.png"

    for videos, it returns a jpg file:
    >>> get_thumb(default_settings, "bar/foo.webm")
    "bar/thumbnails/foo.jpg"
    """

    path, filen = os.path.split(filename)
    name, ext = os.path.splitext(filen)

    # FIXME: replace this list with Video.extensions
    if ext.lower() in ('.mov', '.avi', '.mp4', '.webm', '.ogv'):
        ext = '.jpg'
    return join(path, settings['thumb_dir'], settings['thumb_prefix'] +
                name + settings['thumb_suffix'] + ext)


def read_settings(filename=None):
    """Read settings from a config file in the source_dir root."""

    logger = logging.getLogger(__name__)
    logger.info("Reading settings ...")
    settings = _DEFAULT_CONFIG.copy()

    if filename:
        logger.debug("Settings file: %s", filename)
        settings_path = os.path.dirname(filename)
        tempdict = {}

        with open(filename) as f:
            code = compile(f.read(), filename, 'exec')
            exec(code, tempdict)

        settings.update((k, v) for k, v in tempdict.items()
                        if k not in ['__builtins__'])

        # Make the paths relative to the settings file
        paths = ['source', 'destination']

        if os.path.isdir(join(settings_path, settings['theme'])):
            paths.append('theme')

        enc = locale.getpreferredencoding() if PY2 else None

        for p in paths:
            path = settings[p]
            if path and not isabs(path):
                settings[p] = abspath(normpath(join(settings_path, path)))
                logger.debug("Rewrite %s : %s -> %s", p, path, settings[p])

            # paths must to be unicode strings so that os.walk will return
            # unicode dirnames and filenames
            if PY2 and isinstance(settings[p], str):
                settings[p] = settings[p].decode(enc)

    for key in ('img_size', 'thumb_size', 'video_size'):
        w, h = settings[key]
        if h > w:
            settings[key] = (h, w)
            logger.warning("The %s setting should be specified with the "
                           "largest value first.", key)

    if not settings['img_processor']:
        logger.info('No Processor, images will not be resized')

    logger.debug('Settings:\n%s', pformat(settings, width=120))
    return settings


def create_settings(**kwargs):
    """Create a new default setting copy and initialize it with kwargs."""
    settings = _DEFAULT_CONFIG.copy()
    settings.update(kwargs)
    return settings
