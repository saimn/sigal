# -*- coding:utf-8 -*-

# Copyright (c) 2009-2012 - Simon Conseil

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

from __future__ import absolute_import

__author__ = "Simon Conseil"
__version__ = "0.2"
__license__ = "MIT"

import argparse
import logging
import os
import sys

from logging import Formatter

from .gallery import Gallery
from .settings import read_settings

_DEFAULT_CONFIG_FILE = 'sigal.conf.py'


def init_logging(level=logging.INFO):
    """ Logging config

    Set the level and create a more detailed formatter for debug mode.
    """

    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    if level == logging.DEBUG:
        formatter = Formatter('%(levelname)s - %(message)s')
    else:
        formatter = Formatter('%(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main():
    "main program"

    parser = argparse.ArgumentParser(
        description='simple static gallery generator.')
    parser.add_argument('input_dir', help='input directory')
    parser.add_argument('output_dir', nargs='?', default='_build',
                        help='output directory (default: _build/)')
    parser.add_argument('--version', action='version',
                        version="%(prog)s version " + __version__)
    parser.add_argument("-f", "--force", action='store_true',
                        help="force the reprocessing of existing images")
    parser.add_argument('-v', '--verbose', action='store_const',
                        const=logging.INFO, dest='verbosity',
                        help='show all messages')
    parser.add_argument('-d', '--debug', action='store_const',
                        const=logging.DEBUG, dest='verbosity',
                        help='show all message, including debug messages')
    parser.add_argument("-c", "--config",
                        help="configuration file (default: "
                        "<input_dir>/sigal.conf.py)")
    parser.add_argument("-t", "--theme",
                        help="specify a theme directory, or a theme name for "
                             "the themes included with Sigal")

    args = parser.parse_args()
    level = args.verbosity or logging.WARNING

    init_logging(level=level)
    logger = logging.getLogger(__name__)

    if not os.path.isdir(args.input_dir):
        logger.error("Input directory %s does not exist.", args.input_dir)
        sys.exit(1)

    logger.info("Reading settings ...")
    settings_file = args.config or os.path.join(args.input_dir,
                                                _DEFAULT_CONFIG_FILE)
    if not os.path.isfile(settings_file):
        logger.error("Settings file not found (%s)", settings_file)
        sys.exit(1)
    settings = read_settings(settings_file)

    # create gallery
    gallery = Gallery(settings, args.input_dir, args.output_dir,
                      force=args.force, theme=args.theme)
    gallery.build()
