#!/usr/bin/env python2
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

import os
import codecs
import markdown
import PIL

from distutils.dir_util import copy_tree
from fnmatch import fnmatch
from jinja2 import Environment, PackageLoader
from sigal.image import Image

DEFAULT_THEME = "default"
INDEX_PAGE = "index.html"
DESCRIPTION_FILE = "index.md"
SIGAL_LINK = "https://github.com/saimn/sigal"
PATH_SEP = u" » "
THEMES_PATH = os.path.normpath(os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'themes'))


def do_link(link, title):
    "return html link"
    return '<a href="%s">%s</a>' % (link, title)


class Generator():
    """ Generate html pages for each directory of images """

    def __init__(self, settings, path, theme=DEFAULT_THEME, tpl=INDEX_PAGE):
        self.data = {}
        self.settings = settings
        self.path = os.path.normpath(path)
        self.theme = settings['theme'] or theme

        # search the theme in sigal/theme if the given one does not exists
        if not os.path.exists(self.theme):
            theme_path = os.path.join(THEMES_PATH, self.theme)
            self.theme = theme_path
            if not os.path.exists(theme_path):
                raise Exception("Impossible to find the theme %s" % self.theme)

        theme_relpath = os.path.relpath(self.theme, os.path.dirname(__file__))
        env = Environment(loader=PackageLoader('sigal', theme_relpath))
        self.template = env.get_template(tpl)

        self.ctx = {}
        self.ctx['sigal_link'] = SIGAL_LINK

    def directory_list(self):
        "get the list of directories with files of particular extensions"

        ignored = ['theme', self.settings['bigimg_dir']]
        if self.settings['thumb_dir']:
            ignored.append(self.settings['thumb_dir'])

        for dirpath, dirnames, filenames in os.walk(self.path):
            dirpath = os.path.normpath(dirpath)
            if os.path.split(dirpath)[1] not in ignored and \
                    not fnmatch(dirpath, '*theme*'):
                # sort images and sub-albums by name
                filenames.sort(key=str.lower)
                dirnames.sort(key=str.lower)

                self.data[dirpath] = {}
                self.data[dirpath]['img'] = [f for f in filenames
                                             if os.path.splitext(f)[1] in
                                             self.settings['fileextlist']]
                self.data[dirpath]['subdir'] = [d for d in dirnames
                                                if d not in ignored]

    def find_representative(self, path):
        """
        find the representative image for a given album/path
        at the moment, this is the first image found.
        """

        files = [f for f in os.listdir(path)
                 if os.path.isfile(os.path.join(path, f))
                 and os.path.splitext(f)[1] in self.settings['fileextlist']]

        for f in files:
            # find and return the first landscape image
            im = PIL.Image.open(os.path.join(path, f))
            if im.size[0] > im.size[1]:
                return f

        # else simply return the 1st image
        return files[0]

    def generate(self):
        """
        Render the html page
        """

        # copy static files in the output dir
        theme_outpath = os.path.join(os.path.abspath(self.path), 'theme')
        copy_tree(self.theme, theme_outpath)
        self.ctx['theme'] = {'name': os.path.basename(self.theme)}

        self.directory_list()

        for dirpath in self.data.keys():
            self.data[dirpath].update(get_metadata(dirpath))

        # loop on directories
        for dirpath in self.data.keys():
            self.ctx['theme']['path'] = os.path.relpath(theme_outpath, dirpath)
            dir_relpath = os.path.relpath(self.path, dirpath)
            self.ctx['home_path'] = os.path.join(dir_relpath, INDEX_PAGE)

            # paths to upper directories (with titles and links)
            tmp_path = dirpath
            self.ctx['paths'] = do_link(INDEX_PAGE,
                                        self.data[tmp_path]['title'])

            while tmp_path != self.path:
                tmp_path = os.path.normpath(os.path.join(tmp_path, '..'))
                link = os.path.relpath(tmp_path, dirpath) + "/" + INDEX_PAGE
                self.ctx['paths'] = do_link(link,
                                            self.data[tmp_path]['title']) + \
                    PATH_SEP + self.ctx['paths']

            self.ctx['images'] = []
            for i in self.data[dirpath]['img']:
                image = {
                    'file': i,
                    'thumb': os.path.join(self.settings['thumb_dir'],
                                          self.settings['thumb_prefix'] + i)
                    }
                self.ctx['images'].append(image)

            self.ctx['albums'] = []
            for d in self.data[dirpath]['subdir']:

                dpath = os.path.join(dirpath, d)
                alb_thumb = self.data[dpath].get('representative', '')

                if not alb_thumb or \
                   not os.path.isfile(os.path.join(dpath, alb_thumb)):
                    alb_thumb = self.find_representative(dpath)

                thumb_name = os.path.join(self.settings['thumb_dir'],
                                          self.settings['thumb_prefix'] +
                                          alb_thumb)
                thumb_path = os.path.join(dpath, thumb_name)

                if not os.path.exists(thumb_path):
                    img = Image(os.path.join(dpath, alb_thumb))
                    img.thumbnail(thumb_path, self.settings['thumb_size'],
                                  fit=self.settings['thumb_fit'],
                                  quality=self.settings['jpg_quality'])

                album = {
                    'path': os.path.join(d, INDEX_PAGE),
                    'title': self.data[dpath]['title'],
                    'thumb': os.path.join(d, thumb_name)
                    }
                self.ctx['albums'].append(album)

            page = self.template.render(self.data[dirpath],
                                        **self.ctx).encode('utf-8')

            # save page
            f = open(os.path.join(dirpath, INDEX_PAGE), 'w')
            f.write(page)
            f.close()


def get_metadata(path):
    """ Get album metadata from DESCRIPTION_FILE:

    - title
    - representative image
    - description
    """

    descfile = os.path.join(path, DESCRIPTION_FILE)
    meta = {}

    if not os.path.isfile(descfile):
        # default: get title from directory name
        meta['title'] = os.path.basename(path).replace('_', ' ').\
            replace('-', ' ').capitalize()
    else:
        md = markdown.Markdown(extensions=['meta'])

        with codecs.open(descfile, "r", "utf-8") as f:
            text = f.read()

        html = md.convert(text)

        meta = {
            'title': md.Meta.get('title', [''])[0],
            'description': html,
            'representative': md.Meta.get('representative', [''])[0]
            }

    return meta
