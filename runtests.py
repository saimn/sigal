#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - Piwigo gallery generator
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

"""Run tests for sigal

This script allows to test quickly the creation of a gallery, and prints
additionnal information for debugging purpose.
"""

import os
import sys
from sigal.image import Gallery
from sigal.params import read_params

if __name__ == '__main__':
    print ":: Reading parameters ..."
    params = read_params("./test")

    print ":: params :"
    print params.items('sigal')
    # print "\n".join(["%s=%s" % (k, v) for k, v in params.items()])
    # print "\n"

    # create gallery
    gallery = Gallery(params)

    filelist = gallery.create_gallery("./test", "./test/output")

    print "images     : %s" % filelist[0]
    print "thumbnails : %s" % filelist[1]
    print "big images : %s" % filelist[2]

    sys.exit(0)
