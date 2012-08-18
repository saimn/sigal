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

import os
import ConfigParser

_DEFAULT_CONFIG = {
    'img_size': '640x480',
    'thumb_prefix': '',
    'thumb_size': '150x112',
    'thumb_dir': 'thumbnail',
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

    # Read the default configuration
    config = ConfigParser.ConfigParser(defaults=_DEFAULT_CONFIG)

    # Load the config file
    if filename and os.path.isfile(filename):
        config.read(filename)

    settings = dict(config.items('sigal'))
    settings['jpg_quality'] = int(settings['jpg_quality'])
    settings['fileextlist'] = settings['fileextlist'].split(',')
    settings['img_size'] = get_size(settings['img_size'])
    settings['thumb_size'] = get_size(settings['thumb_size'])

    if settings['exif']:
        try:
            import pyexiv2
        except ImportError:
            settings['exif'] = 0
            print "Error: install pyexiv2 module to use exif metadatas."

    return settings
