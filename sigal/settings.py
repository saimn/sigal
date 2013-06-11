# -*- coding:utf-8 -*-

# Copyright (c) 2009-2013 - Simon Conseil

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

import logging
import os

_DEFAULT_CONFIG = {
    'source': '',
    'destination': '_build',
    'img_size': (640, 480),
    'img_processor': 'ResizeToFit',
    'make_thumbs': True,
    'thumb_prefix': '',
    'thumb_suffix': '',
    'thumb_size': (200, 150),
    'thumb_dir': 'thumbnails',
    'thumb_fit': True,
    'keep_orig': False,
    'orig_dir': 'original',
    'jpg_options': {'quality': 85, 'optimize': True, 'progressive': True},
    'copyright': '',
    'ext_list': ['.jpg', '.jpeg', '.JPG', '.JPEG', '.png'],
    'theme': 'colorbox',
    'write_html': True,
    'index_in_url': False,
    'links': '',
    'google_analytics': ''
}


def get_thumb(settings, filename):
    """Return the path to the thumb."""

    path, filen = os.path.split(filename)
    name, ext = os.path.splitext(filen)
    return os.path.join(path, settings['thumb_dir'], settings['thumb_prefix'] +
                        name + settings['thumb_suffix'] + ext)


def get_orig(settings, filename):
    """Return the path to the original image."""

    path, filen = os.path.split(filename)
    return os.path.join(path, settings['orig_dir'], filen)


def read_settings(filename=None):
    """Read settings from a config file in the source_dir root."""

    logger = logging.getLogger(__name__)
    logger.info("Reading settings ...")
    settings = _DEFAULT_CONFIG.copy()
    settings_path = os.path.dirname(filename)

    if filename:
        logger.debug("Settings file: %s", filename)
        tempdict = {}
        execfile(filename, tempdict)
        settings.update((k, v) for k, v in tempdict.iteritems()
                        if k not in ['__builtins__'])

        # Make the paths relative to the settings file
        paths = ['source', 'destination']

        if os.path.isdir(os.path.join(settings_path, settings['theme'])):
            paths.append('theme')

        for p in paths:
            path = settings[p]
            if path and not os.path.isabs(path):
                settings[p] = os.path.abspath(os.path.normpath(os.path.join(
                    settings_path, path)))
                logger.debug("Rewrite %s : %s -> %s", p, path, settings[p])

    for key in ('img_size', 'thumb_size'):
        w, h = settings[key]
        if h > w:
            settings[key] = (h, w)
            logger.warning("The %s setting should be specified with the "
                           "largest value first.", key)

    return settings
