# -*- coding:utf-8 -*-

# Copyright (c) 2009-2013 - Simon Conseil

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

import codecs
import logging
import os
import sys
import locale
from argh import ArghParser, arg
from logging import Formatter

from .gallery import Gallery
from .pkgmeta import __version__
from .settings import read_settings

_DEFAULT_CONFIG_FILE = 'sigal.conf.py'


def init_logging(level=logging.INFO):
    """Logging config

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


def init():
    """Copy a sample config file in the current directory."""

    from pkg_resources import resource_string
    conf = resource_string(__name__, 'templates/sigal.conf.py')

    with codecs.open('sigal.conf.py', 'w', 'utf-8') as f:
        f.write(conf)
    print "Sample config file created: sigal.conf.py"


@arg('source', nargs='?', help='Input directory')
@arg('destination', nargs='?', help='Output directory (default: _build/)')
@arg('-f', '--force', help="Force the reprocessing of existing images")
@arg('-v', '--verbose', help="Show all messages")
@arg('-d', '--debug', help="Show all message, including debug messages")
@arg('-c', '--config', help="Configuration file (default: sigal.conf.py in "
     "the current working directory)")
@arg('-t', '--theme', help="Specify a theme directory, or a theme name for "
     "the themes included with Sigal")
def build(source, destination, debug=False, verbose=False, force=False,
          config=None, theme=None):
    """Run sigal to process a directory. """

    level = ((debug and logging.DEBUG) or (verbose and logging.INFO)
             or logging.WARNING)
    init_logging(level=level)
    logger = logging.getLogger(__name__)

    settings_file = config or _DEFAULT_CONFIG_FILE
    if not os.path.isfile(settings_file):
        logger.error("Settings file not found (%s)", settings_file)
        sys.exit(1)
    settings = read_settings(settings_file)

    if source:
        settings['source'] = os.path.abspath(source)
    if destination:
        settings['destination'] = os.path.abspath(destination)

    logger.info("Input  : %s", settings['source'])
    if not settings['source'] or not os.path.isdir(settings['source']):
        logger.error("Input directory '%s' does not exist.",
                     settings['source'])
        sys.exit(1)

    logger.info("Output : %s", settings['destination'])
    if not os.path.relpath(settings['destination'],
                           settings['source']).startswith('..'):
        logger.error("Output directory should be outside of the input "
                     "directory.")
        sys.exit(1)

    locale.setlocale(locale.LC_ALL, settings['locale'])
    gal = Gallery(settings, force=force, theme=theme)
    gal.build()


@arg('path', nargs='?', default='_build',
     help='Directory to serve (default: _build/)')
def serve(path):
    """Run a simple web server."""

    import SimpleHTTPServer
    import SocketServer

    if os.path.exists(path):
        os.chdir(path)
        PORT = 8000
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.TCPServer(("", PORT), Handler, False)

        print " * Running on http://127.0.0.1:%i/" % PORT

        try:
            httpd.allow_reuse_address = True
            httpd.server_bind()
            httpd.server_activate()
            httpd.serve_forever()
        except KeyboardInterrupt:
            print '\nAll done!'
    else:
        sys.stderr.write("The '%s' directory doesn't exist.\n" % path)


def main():
    parser = ArghParser(description='Simple static gallery generator.',
                        version=__version__)
    parser.add_commands([init, build, serve])
    parser.dispatch()
