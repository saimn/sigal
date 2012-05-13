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
sigal - simple static gallery generator
=======================================

sigal is yet another python script to prepare a static gallery of images:

* resize images, create thumbnails with some options (squared thumbs, ...).
* generate html pages.
"""

__author__ = "Saimon (contact at saimon dot org)"
__version__ = "0.1"
__date__ = "20110513"
__copyright__ = "Copyright (C) 2009-2012 - saimon.org"
__license__ = "GPL"

import os
import sys
import argparse
from sigal.image import Gallery
from sigal.params import read_params
from sigal.theme import Theme

def main():
    "main program"

    version = "version %s, %s" % (__version__, __date__)

    parser = argparse.ArgumentParser(description='simple static gallery generator.')
    parser.add_argument('input_dir', help='input directory')
    parser.add_argument('output_dir', help='output directory')
    parser.add_argument('--version', action='version',
                        version="%(prog)s " + version)
    parser.add_argument('-c', '--copyright',
                        help="copyright message added to the images")
    parser.add_argument("-f", "--force", action='store_true',
                        help="force the reprocessing of existing images and thumbnails")

    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print "Directory %s does not exist." % args.input_dir
        sys.exit(1)

    print ":: Reading parameters ..."
    params = read_params(args.input_dir)

    if args.copyright:
        params.set('sigal', 'copyright', args.copyright)

    # create gallery
    gallery = Gallery(params)
    gallery.build(args.input_dir, args.output_dir, force=args.force)

    r = Theme(params, args.output_dir)
    r.render()

    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
