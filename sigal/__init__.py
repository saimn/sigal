# -*- coding:utf-8 -*-

# Copyright (c) 2009-2014 - Simon Conseil

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

from __future__ import absolute_import, print_function

import click
import importlib
import io
import locale
import logging
import os
import sys
import time

from click import argument, option

from .compat import server, socketserver, string_types
from .gallery import Gallery
from .log import init_logging
from .pkgmeta import __version__
from .settings import read_settings
from .utils import copy

_DEFAULT_CONFIG_FILE = 'sigal.conf.py'


@click.group()
@click.version_option(version=__version__)
def main():
    """Sigal - Simple Static Gallery Generator.

    Sigal is yet another python script to prepare a static gallery of images:
    resize images, create thumbnails with some options, generate html pages.

    """
    pass


@main.command()
@argument('path', default=_DEFAULT_CONFIG_FILE)
def init(path):
    """Copy a sample config file in the current directory (default to
    'sigal.conf.py'), or use the provided 'path'."""

    if os.path.isfile(path):
        print("Found an existing config file, will abort to keep it safe.")
        sys.exit(1)

    from pkg_resources import resource_string
    conf = resource_string(__name__, 'templates/sigal.conf.py')

    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(conf.decode('utf8'))
    print("Sample config file created: {}".format(path))


@main.command()
@argument('source', required=False)
@argument('destination', required=False)
@option('-f', '--force', is_flag=True,
        help="Force the reprocessing of existing images")
@option('-v', '--verbose', is_flag=True, help="Show all messages")
@option('-d', '--debug', is_flag=True,
        help="Show all message, including debug messages")
@option('-c', '--config', default=_DEFAULT_CONFIG_FILE, show_default=True,
        help="Configuration file")
@option('-t', '--theme', help="Specify a theme directory, or a theme name for "
        "the themes included with Sigal")
@option('--title', help="Title of the gallery (overrides the title setting.")
@option('-n', '--ncpu', help="Number of cpu to use (default: all)")
def build(source, destination, debug, verbose, force, config, theme, title,
          ncpu):
    """Run sigal to process a directory.

    If provided, 'source', 'destination' and 'theme' will override the
    corresponding values from the settings file.

    """
    level = ((debug and logging.DEBUG) or (verbose and logging.INFO)
             or logging.WARNING)
    init_logging(__name__, level=level)
    logger = logging.getLogger(__name__)

    if not os.path.isfile(config):
        logger.error("Settings file not found: %s", config)
        sys.exit(1)

    start_time = time.time()
    settings = read_settings(config)

    for key in ('source', 'destination', 'theme'):
        arg = locals()[key]
        if arg is not None:
            settings[key] = os.path.abspath(arg)
        logger.info("%12s : %s", key.capitalize(), settings[key])

    if not settings['source'] or not os.path.isdir(settings['source']):
        logger.error("Input directory not found: %s", settings['source'])
        sys.exit(1)

    if not os.path.relpath(settings['destination'],
                           settings['source']).startswith('..'):
        logger.error("Output directory should be outside of the input "
                     "directory.")
        sys.exit(1)

    if title:
        settings['title'] = title

    locale.setlocale(locale.LC_ALL, settings['locale'])
    init_plugins(settings)

    gal = Gallery(settings, ncpu=ncpu)
    gal.build(force=force)

    # copy extra files
    for src, dst in settings['files_to_copy']:
        src = os.path.join(settings['source'], src)
        dst = os.path.join(settings['destination'], dst)
        logger.debug('Copy %s to %s', src, dst)
        copy(src, dst, symlink=settings['orig_link'])

    print(('Done.\nProcessed {image} images ({image_skipped} skipped) and '
           '{video} videos ({video_skipped} skipped) in {duration:.2f} '
           'seconds.').format(duration=time.time() - start_time, **gal.stats))


def init_plugins(settings):
    """Load plugins and call register()."""

    logger = logging.getLogger(__name__)
    logger.debug('Plugin paths: %s', settings['plugin_paths'])

    for path in settings['plugin_paths']:
        sys.path.insert(0, path)

    for plugin in settings['plugins']:
        try:
            if isinstance(plugin, string_types):
                mod = importlib.import_module(plugin)
                mod.register(settings)
            else:
                plugin.register(settings)
            logger.debug('Registered plugin %s', plugin)
        except Exception as e:
            logger.error('Failed to load plugin %s: %r', plugin, e)

    for path in settings['plugin_paths']:
        sys.path.remove(path)


@main.command()
@argument('destination', default='_build')
@option('-p', '--port', help="Port to use", default=8000)
@option('-c', '--config', default=_DEFAULT_CONFIG_FILE, 
        show_default=True, help='Configuration file')
def serve(destination, port, config):
    """Run a simple web server."""
    if os.path.exists(destination):
        pass
    elif os.path.exists(config):
        settings = read_settings(config)
        destination = settings.get('destination')
        if not os.path.exists(destination):
            sys.stderr.write("The '{}' directory doesn't exist, "
                             "maybe try building first?"
                             "\n".format(destination))
            sys.exit(1)
    else:
        sys.stderr.write("The {destination} directory doesn't exist "
                         "and the config file ({config}) could not be "
                         "read."
                         "\n".format(destination=destination, config=config))
        sys.exit(2)

    print('DESTINATION : {}'.format(destination))
    os.chdir(destination)
    Handler = server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), Handler, False)
    print(" * Running on http://127.0.0.1:{}/".format(port))

    try:
        httpd.allow_reuse_address = True
        httpd.server_bind()
        httpd.server_activate()
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nAll done!')

