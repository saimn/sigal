#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# Copyright (c) 2009-2012 - Simon C. (saimon.org)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

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
__license__ = "MIT"

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
    parser.add_argument("-f", "--force", action='store_true',
                        help="force the reprocessing of existing images")

    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print "Directory %s does not exist." % args.input_dir
        sys.exit(1)

    print ":: Reading settings ..."
    settings = read_settings(os.path.join(args.input_dir,
                                          _DEFAULT_CONFIG_FILE))

    # create gallery
    gallery = Gallery(settings, args.input_dir)
    gallery.build(args.output_dir, force=args.force)

    r = Generator(settings, args.output_dir)
    r.generate()
