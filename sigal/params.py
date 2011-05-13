#!/usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - simple static gallery generator
# Copyright (C) 2009-2011 - Simon C. (saimon.org)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; If not, see http://www.gnu.org/licenses/

"""Parameters utils"""

import os
import ConfigParser

CONFIGFILE = '~/.config/sigal/sigal.conf'
SOURCEDIR_CONFIGFILE = 'sigal.conf'
CONFIGDEFAULTS = {
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

def read_params(source_dir):
    "Read params from a config file"

    # Read configuration file
    config = ConfigParser.ConfigParser(defaults = CONFIGDEFAULTS)
    config.read(os.path.expanduser(CONFIGFILE))

    # Load a config file in the source_dir root
    sourcedir_configfile = os.path.join(source_dir, SOURCEDIR_CONFIGFILE)
    if os.path.isfile(sourcedir_configfile):
        config.read(sourcedir_configfile)

    return config
