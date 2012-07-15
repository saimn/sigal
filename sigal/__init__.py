#! /usr/bin/env python2
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

"""
sigal - simple static gallery generator
=======================================

sigal is yet another python script to prepare a static gallery of images:

* resize images, create thumbnails with some options (squared thumbs, ...).
* generate html pages.
"""

__author__ = "Saimon (contact at saimon dot org)"
__version__ = "0.1-dev"
__copyright__ = "Copyright (C) 2009-2012 - saimon.org"
__license__ = "GPL"

import os
import sys
import argparse
from sigal.image import Gallery
from sigal.settings import read_settings
from sigal.generator import Generator

_DEFAULT_CONFIG_FILE = 'sigal.conf'

def main():
    "main program"

    parser = argparse.ArgumentParser(description='simple static gallery generator.')
    parser.add_argument('input_dir', help='input directory')
    parser.add_argument('output_dir', help='output directory')
    parser.add_argument('--version', action='version',
                        version="%(prog)s version " + __version__)
    parser.add_argument('-c', '--copyright',
                        help="copyright message added to the images")
    parser.add_argument("-f", "--force", action='store_true',
                        help="force the reprocessing of existing images")

    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print "Directory %s does not exist." % args.input_dir
        sys.exit(1)

    print ":: Reading settings ..."
    settings = read_settings(os.path.join(args.input_dir, _DEFAULT_CONFIG_FILE))

    if args.copyright:
        settings['copyright'] = args.copyright

    # create gallery
    gallery = Gallery(settings, args.input_dir)
    gallery.build(args.output_dir, force=args.force)

    r = Generator(settings, args.output_dir)
    r.generate()
