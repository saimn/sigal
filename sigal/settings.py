#!/usr/bin/env python2
# -*- coding:utf-8 -*-

# Copyright (c) 2009-2012 - Simon C. (saimon.org)

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

import ConfigParser
import logging
import os


_DEFAULT_CONFIG = {
    'img_size': '640x480',
    'make_thumbs': 1,
    'thumb_prefix': 'TN-',
    'thumb_size': '150x112',
    'thumb_dir': '',
    'thumb_fit': 1,
    'big_img': 0,
    'bigimg_dir': 'big',
    'jpg_quality': 90,
    'exif': 0,
    'copyright': '',
    'fileExtList': '.jpg,.jpeg,.JPG,.JPEG,.png',
    'theme': 'default'
    }


def get_size(string):
    "split size string to a tuple of int"
    size = [int(i) for i in string.split("x")]
    if size[1] > size[0]:
        size[0], size[1] = size[1], size[0]
    return tuple(size)


def read_settings(filename=None):
    "Read settings from a config file in the source_dir root"

    logger = logging.getLogger(__name__)

    # Read the default configuration
    config = ConfigParser.ConfigParser(defaults=_DEFAULT_CONFIG)

    # Load the config file
    if filename and os.path.isfile(filename):
        config.read(filename)

    settings = dict(config.items('sigal'))
    settings['fileextlist'] = settings['fileextlist'].split(',')
    settings['img_size'] = get_size(settings['img_size'])
    settings['thumb_size'] = get_size(settings['thumb_size'])

    settings['jpg_quality'] = config.getint('sigal', 'jpg_quality')
    settings['big_img'] = config.getboolean('sigal', 'big_img')
    settings['exif'] = config.getboolean('sigal', 'exif')
    settings['make_thumbs'] = config.getboolean('sigal', 'make_thumbs')
    settings['thumb_fit'] = config.getboolean('sigal', 'thumb_fit')

    if settings['exif']:
        try:
            import pyexiv2
        except ImportError:
            settings['exif'] = 0
            logger.error("Error: install pyexiv2 module to use exif metadatas")

    return settings
