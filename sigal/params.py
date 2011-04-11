#!/usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - Piwigo gallery generator
# Copyright (C) 2009-2011 Simon - saimon.org
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

from configobj import ConfigObj

def read_params(config_file):
    "Read params from a config file"

    params = ConfigObj(config_file,file_error=True)

    # convert types
    params["im_width"] = int(params["im_width"])
    params["im_height"] = int(params["im_height"])
    params["thumb_width"] = int(params["thumb_width"])
    params["thumb_height"] = int(params["thumb_height"])
    params["bigimg"] = int(params["bigimg"])
    params["squarethumb"] = int(params["squarethumb"])
    params["jpgquality"] = int(params["jpgquality"])
    params["exif"] = int(params["exif"])
    params["copyright"] = int(params["copyright"])
    return params
