#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# pywiUpload - Piwigo gallery generator
# Copyright (C) 2009-2011 - saimon.org
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

"""Run tests for pywiUpload

This script allows to test quickly the creation of a gallery, and prints
additionnal information for debugging purpose.
"""

import os
import sys
import pywiUpload
from pywiupload.image import Gallery

if __name__ == '__main__':
    # read params from config file
    config_file = os.path.join(sys.path[0], 'pywiUpload.conf')

    print ":: Reading parameters ..."
    params = pywiUpload.read_params(config_file)

    print "\n".join(["%s=%s" % (k, v) for k, v in params.items()])
    print "\n"

    # create gallery
    gallery = Gallery(params)

    filelist = gallery.create_gallery("./test", "./test/output")

    print "images     : %s" % filelist[0]
    print "thumbnails : %s" % filelist[1]
    print "big images : %s" % filelist[2]

    sys.exit(0)
