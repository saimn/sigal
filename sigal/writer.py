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
Generate html pages for each directory of images
"""

from __future__ import absolute_import

import codecs
import copy
import os

from os.path import abspath
from distutils.dir_util import copy_tree
from jinja2 import Environment, PackageLoader

from .image import Image

INDEX_PAGE = "index.html"
SIGAL_LINK = "https://github.com/saimn/sigal"
PATH_SEP = u" » "
THEMES_PATH = os.path.normpath(os.path.join(
    abspath(os.path.dirname(__file__)), 'themes'))


def do_link(link, title):
    "Return a html link"
    return '<a href="%s">%s</a>' % (link, title)


class Writer():
    """ Generate html pages for each directory of images """

    def __init__(self, settings, output_dir, theme='default'):
        self.settings = settings
        self.output_dir = os.path.abspath(output_dir)
        self.theme = settings['theme'] or theme

        # search the theme in sigal/theme if the given one does not exists
        if not os.path.exists(self.theme):
            theme_path = os.path.join(THEMES_PATH, self.theme)
            self.theme = theme_path
            if not os.path.exists(theme_path):
                raise Exception("Impossible to find the theme %s" % self.theme)

        theme_relpath = os.path.relpath(self.theme, os.path.dirname(__file__))
        env = Environment(loader=PackageLoader('sigal', theme_relpath))
        self.template = env.get_template(INDEX_PAGE)

        self.copy_assets()

        self.ctx = {
            'sigal_link': SIGAL_LINK,
            'theme': {'name': os.path.basename(self.theme)},
            'images': [],
            'albums': [],
        }

    def copy_assets(self):
        "Copy the theme files in the output dir"

        self.theme_path = os.path.join(self.output_dir, 'theme')
        copy_tree(self.theme, self.theme_path)

    def write(self, paths, relpath):
        """
        Render the html page
        """

        path = os.path.join(self.output_dir, relpath)

        ctx = copy.deepcopy(self.ctx)
        ctx['theme']['path'] = os.path.relpath(self.theme_path, path)
        ctx['home_path'] = os.path.join(
            os.path.relpath(self.output_dir, path), INDEX_PAGE)

        # paths to upper directories (with titles and links)
        tmp_path = relpath
        ctx['paths'] = do_link(INDEX_PAGE, paths[tmp_path]['title'])

        while tmp_path != '.':
            tmp_path = os.path.normpath(os.path.join(tmp_path, '..'))
            link = os.path.relpath(tmp_path, relpath) + "/" + INDEX_PAGE
            ctx['paths'] = do_link(link, paths[tmp_path]['title']) + \
                           PATH_SEP + ctx['paths']

        for i in paths[relpath]['img']:
            ctx['images'].append({
                'file': i,
                'thumb': os.path.join(self.settings['thumb_dir'],
                                      self.settings['thumb_prefix'] + i)
            })

        for d in paths[relpath]['subdir']:
            dpath = os.path.normpath(os.path.join(relpath, d))
            alb_thumb = paths[dpath]['representative']
            thumb_name = os.path.join(self.settings['thumb_dir'],
                                      self.settings['thumb_prefix'] +
                                      alb_thumb)
            thumb_path = os.path.join(self.output_dir, dpath, thumb_name)

            # generate the thumbnail if it is missing (if
            # settings['make_thumbs'] is False)
            if not os.path.exists(thumb_path):
                img = Image(os.path.join(self.output_dir, dpath, alb_thumb))
                img.thumbnail(thumb_path, self.settings['thumb_size'],
                              fit=self.settings['thumb_fit'],
                              quality=self.settings['jpg_quality'])

            ctx['albums'].append({
                'path': os.path.join(d, INDEX_PAGE),
                'title': paths[dpath]['title'],
                'thumb': os.path.join(d, thumb_name)
            })

        # generate html page and save
        page = self.template.render(paths[relpath], **ctx)

        with codecs.open(os.path.join(path, INDEX_PAGE), 'w', 'utf-8') as f:
            f.write(page)
