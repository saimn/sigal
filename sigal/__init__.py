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

from __future__ import absolute_import, print_function

import io
import locale
import logging
import os
import sys
import time

from argh import ArghParser, arg

from .gallery import Gallery
from .log import init_logging
from .pkgmeta import __version__
from .settings import read_settings
from .utils import copy

_DEFAULT_CONFIG_FILE = 'sigal.conf.py'


@arg('path', nargs='?', help='Path of the sample config file')
def init(path):
    """Copy a sample config file in the current directory."""

    from pkg_resources import resource_string
    path = path or 'sigal.conf.py'
    conf = resource_string(__name__, 'templates/sigal.conf.py')

    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(conf.decode('utf8'))
    print("Sample config file created: {}".format(path))


@arg('source', nargs='?', help='Input directory')
@arg('destination', nargs='?', help='Output directory (default: _build/)')
@arg('-f', '--force', help="Force the reprocessing of existing images")
@arg('-v', '--verbose', help="Show all messages")
@arg('-d', '--debug', help="Show all message, including debug messages")
@arg('-c', '--config', help="Configuration file")
@arg('-t', '--theme', help="Specify a theme directory, or a theme name for "
     "the themes included with Sigal")
@arg('-n', '--ncpu', help="Number of cpu to use (default: all)")
def build(source, destination, debug=False, verbose=False, force=False,
          config=_DEFAULT_CONFIG_FILE, theme=None, ncpu=None):
    """Run sigal to process a directory. """

    level = ((debug and logging.DEBUG) or (verbose and logging.INFO)
             or logging.WARNING)
    init_logging(__name__, level=level)
    logger = logging.getLogger(__name__)

    start_time = time.time()
    if not os.path.isfile(config):
        logger.error("Settings file not found: %s", config)
        sys.exit(1)
    settings = read_settings(config)

    if source:
        settings['source'] = os.path.abspath(source)
    if destination:
        settings['destination'] = os.path.abspath(destination)

    logger.info("Input  : %s", settings['source'])
    if not settings['source'] or not os.path.isdir(settings['source']):
        logger.error("Input directory not found: %s", settings['source'])
        sys.exit(1)

    logger.info("Output : %s", settings['destination'])
    if not os.path.relpath(settings['destination'],
                           settings['source']).startswith('..'):
        logger.error("Output directory should be outside of the input "
                     "directory.")
        sys.exit(1)

    locale.setlocale(locale.LC_ALL, settings['locale'])
    gal = Gallery(settings, force=force, theme=theme, ncpu=ncpu)
    gal.build()

    # copy extra files
    for src, dst in settings['files_to_copy']:
        src = os.path.join(settings['source'], src)
        dst = os.path.join(settings['destination'], dst)
        logger.debug('Copy %s to %s', src, dst)
        copy(src, dst, symlink=settings['orig_link'])

    print(('Done.\nProcessed {image} images ({image_skipped} skipped) and '
           '{video} videos ({video_skipped} skipped) in {duration:.2f} '
           'seconds.').format(duration=time.time() - start_time, **gal.stats))


@arg('path', nargs='?', default='_build',
     help='Directory to serve (default: _build/)')
def serve(path):
    """Run a simple web server."""

    if os.path.exists(path):
        from .compat import server, socketserver

        os.chdir(path)
        PORT = 8000
        Handler = server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", PORT), Handler, False)

        print(" * Running on http://127.0.0.1:{}/".format(PORT))

        try:
            httpd.allow_reuse_address = True
            httpd.server_bind()
            httpd.server_activate()
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nAll done!')
    else:
        sys.stderr.write("The '%s' directory doesn't exist.\n" % path)


def main():
    parser = ArghParser(description='Simple static gallery generator.')
    parser.add_commands([init, build, serve])
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    parser.dispatch()
