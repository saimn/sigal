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

CONFIG_FILE = 'sigal.conf'

_DEFAULT_CONFIG = {
    'img_size': '640x480',
    'thumb_prefix': '',
    'thumb_size': '150x112',
    'thumb_dir': "thumbnail",
    'square_thumb': 0,
    'big_img': 0,
    'bigimg_dir': "big",
    'jpg_quality': 90,
    'exif': 1,
    'copyright': '',
    'fileExtList': ".jpg,.jpeg,.JPG,.JPEG,.png"
    }


def read_settings(source_dir):
    "Read settings from a config file in the source_dir root"

    # Read configuration file
    config = ConfigParser.ConfigParser(defaults=_DEFAULT_CONFIG)

    # Load a config file in the source_dir root
    config = os.path.join(source_dir, CONFIG_FILE)
    if os.path.isfile(config):
        config.read(config)

    return config
