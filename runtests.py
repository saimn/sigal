#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - simple static gallery generator
# Copyright (C) 2009-2012 - Simon C. (saimon.org)
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

"""
Run tests for sigal
===================

This script allows to test quickly the creation of a gallery, and prints
additionnal information for debugging purpose.
"""

import sys
from sigal.image import Gallery
from sigal.params import read_params
from sigal.theme import Theme

if __name__ == '__main__':
    print ":: Reading parameters ..."
    params = read_params("./test")

    print ":: params :"
    for i,j in params.items('sigal'):
        print "%s\t = %s" % (i,j)
    print "\n"

    # create gallery
    gallery = Gallery(params)
    gallery.build("./test", "./output")

    # print "images     : %s" % filelist[0]
    # print "thumbnails : %s" % filelist[1]
    # print "big images : %s" % filelist[2]

    r = Theme(params, "./output")
    r.render()
    sys.exit(0)
