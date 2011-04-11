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

"""Prepare and upload a gallery of images for Piwigo

This script resize images, create thumbnails with some options
(rename images, squared thumbs, ...).
"""

__author__ = "Saimon (contact at saimon dot org)"
__version__ = "0.1-dev"
__date__ = "20110411"
__copyright__ = "Copyright (C) 2009-2011 - saimon.org"
__license__ = "GPL"

import os
import sys
from optparse import OptionParser
from sigal.image import Gallery
from sigal.params import read_params

def main():
    "main program"

    # command line options
    usage = "usage: %prog [options] inputdir outputdir"
    version = "version %s, %s" % (__version__, __date__)

    parser = OptionParser(usage=usage, version="%prog "+version)

    parser.add_option("-c", "--copyright", dest="copyright",
                      help="copyright message added to the images")
    parser.add_option("-r", "--rename", dest="rename",
                      help="rename files - specify the basename for renaming")

    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.print_help()
        sys.exit()

    input_dir = args[0]
    output_dir = args[1]

    if not os.path.isdir(input_dir):
        print "Directory %s does not exist." % input_dir
        sys.exit(1)

    # if not os.path.isdir(output_dir):
    #     print "Create %s" % output_dir
    #     os.makedirs(output_dir)

    print ":: Reading parameters ..."
    params = read_params(input_dir)

    if options.copyright:
        params.set('sigal', 'copyright', options.copyright)

    # create gallery
    gallery = Gallery(params)
    out_filelist = gallery.build(input_dir, output_dir)

    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
