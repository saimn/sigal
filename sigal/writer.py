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
Generate html pages for each directory of images.
"""

from __future__ import absolute_import

import codecs
import copy
import logging
import os
import sys

from clint.textui import colored
from distutils.dir_util import copy_tree
from jinja2 import (Environment, PackageLoader, FileSystemLoader, ChoiceLoader,
                    PrefixLoader)
from jinja2.exceptions import TemplateNotFound
from os.path import abspath

from .image import Image
from .settings import get_thumb

INDEX_PAGE = "index.html"
SIGAL_LINK = "https://github.com/saimn/sigal"
PATH_SEP = u" » "
THEMES_PATH = os.path.normpath(os.path.join(
    abspath(os.path.dirname(__file__)), 'themes'))


def link(url, title):
    "Return a html link"
    return '<a href="%s">%s</a>' % (url, title)


class Writer():
    """Generate html pages for each directory of images."""

    def __init__(self, settings, output_dir, theme=None):
        self.settings = settings
        self.output_dir = os.path.abspath(output_dir)
        self.theme = theme or settings['theme']
        self.logger = logging.getLogger(__name__)

        # search the theme in sigal/theme if the given one does not exists
        if not os.path.exists(self.theme):
            self.theme = os.path.join(THEMES_PATH, self.theme)
            if not os.path.exists(self.theme):
                raise Exception("Impossible to find the theme %s" % self.theme)

        self.logger.info("Theme path : %s", self.theme)
        theme_relpath = os.path.join(self.theme, 'templates')
        theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'themes')
        default_loader = FileSystemLoader(os.path.join(theme_path, 'default',
                                                       'templates'))

        env = Environment(
            loader=ChoiceLoader([
                FileSystemLoader(theme_relpath),
                default_loader,  # implicit inheritance
                PrefixLoader({'!default': default_loader})  # explicit one
            ]),
            trim_blocks=True,
        )

        try:
            self.template = env.get_template(INDEX_PAGE)
        except TemplateNotFound:
            self.logger.error(colored.red('ERROR:') +
                              ' The index.html template was not found.')
            sys.exit(1)

        self.copy_assets()

        self.ctx = {
            'sigal_link': SIGAL_LINK,
            'theme': {'name': os.path.basename(self.theme)},
            'images': [],
            'albums': [],
            'breadcumb': ''
        }

    def copy_assets(self):
        """Copy the theme files in the output dir."""

        self.theme_path = os.path.join(self.output_dir, 'static')
        copy_tree(os.path.join(self.theme, 'static'), self.theme_path)

    def write(self, paths, relpath):
        """Render the html page."""

        path = os.path.join(self.output_dir, relpath)
        index_url = os.path.relpath(self.output_dir, path) + '/'
        self.logger.info("Output path : %s", path)

        ctx = copy.deepcopy(self.ctx)
        ctx.update({
            'settings': self.settings,
            'index_url': index_url,
            'index_link': link(index_url, paths['.']['title'])
        })
        ctx['theme']['url'] = os.path.relpath(self.theme_path, path)

        # paths to upper directories (with titles and links)
        if relpath != '.':
            tmp_path = relpath
            breadcumb = [link('.', paths[tmp_path]['title'])]

            while True:
                tmp_path = os.path.normpath(os.path.join(tmp_path, '..'))
                if tmp_path == '.':
                    break

                url = os.path.relpath(tmp_path, relpath) + '/'
                breadcumb.append(link(url, paths[tmp_path]['title']))

            ctx['breadcumb'] = PATH_SEP.join(reversed(breadcumb))

        for i in paths[relpath]['img']:
            ctx['images'].append({'file': i,
                                  'thumb': get_thumb(self.settings, i)})

        for d in paths[relpath]['subdir']:
            dpath = os.path.normpath(os.path.join(relpath, d))
            alb_thumb = paths[dpath]['representative']
            thumb_name = get_thumb(self.settings, alb_thumb)
            thumb_path = os.path.join(self.output_dir, dpath, thumb_name)
            self.logger.debug("Representative path : %s", thumb_path)

            # generate the thumbnail if it is missing (if
            # settings['make_thumbs'] is False)
            if not os.path.exists(thumb_path):
                img = Image(os.path.join(self.output_dir, dpath, alb_thumb))
                img.thumbnail(thumb_path, self.settings['thumb_size'],
                              fit=self.settings['thumb_fit'],
                              quality=self.settings['jpg_quality'])

            ctx['albums'].append({
                'url': d + '/',
                'title': paths[dpath]['title'],
                'thumb': os.path.join(d, thumb_name)
            })

        # generate html page and save
        page = self.template.render(paths[relpath], **ctx)

        with codecs.open(os.path.join(path, INDEX_PAGE), 'w', 'utf-8') as f:
            f.write(page)
