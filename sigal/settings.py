#!/usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - simple static gallery generator
# Copyright (C) 2009-2012 - Simon C. (saimon.org)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; If not, see http://www.gnu.org/licenses/

import os
import ConfigParser

_DEFAULT_CONFIG = {
    'img_size': '640x480',
    'thumb_prefix': '',
    'thumb_size': '150x112',
    'thumb_dir': 'thumbnail',
    'square_thumb': 0,
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

    return settings
