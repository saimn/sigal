# -*- coding:utf-8 -*-

# Copyright (c) 2009-2013 - Simon Conseil
# Copyright (c)      2013 - Christophe-Marie Duquesne

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

from __future__ import absolute_import

import codecs
import copy
import jinja2
import logging
import os
import sys

from distutils.dir_util import copy_tree
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, PrefixLoader
from jinja2.exceptions import TemplateNotFound

import sigal.image
import sigal.video
from .settings import get_thumb, get_orig
from .pkgmeta import __url__ as sigal_link

THEMES_PATH = os.path.normpath(os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'themes'))


class Writer(object):
    """Generate html pages for each directory of images."""

    def __init__(self, settings, output_dir, theme=None,
                 template_file="index.html", output_file="index.html"):
        self.settings = settings
        self.output_dir = os.path.abspath(output_dir)
        self.theme = theme or settings['theme']
        self.template_file = template_file
        self.output_file = output_file
        self.logger = logging.getLogger(__name__)

        # optionally add index.html to the URLs
        self.url_ext = self.output_file if settings['index_in_url'] else ''

        # search the theme in sigal/theme if the given one does not exists
        if not os.path.exists(self.theme):
            self.theme = os.path.join(THEMES_PATH, self.theme)
            if not os.path.exists(self.theme):
                raise Exception("Impossible to find the theme %s" % self.theme)

        self.logger.info("Theme  : %s", self.theme)
        theme_relpath = os.path.join(self.theme, 'templates')
        default_loader = FileSystemLoader(
            os.path.join(THEMES_PATH, 'default', 'templates'))

        # setup jinja env
        env_options = {'trim_blocks': True}
        try:
            if tuple(int(x) for x in jinja2.__version__.split('.')) >= (2, 7):
                env_options['lstrip_blocks'] = True
        except ValueError:
            pass

        env = Environment(
            loader=ChoiceLoader([
                FileSystemLoader(theme_relpath),
                default_loader,  # implicit inheritance
                PrefixLoader({'!default': default_loader})  # explicit one
            ]),
            **env_options
        )

        try:
            self.template = env.get_template(self.template_file)
        except TemplateNotFound:
            self.logger.error('The index.html template was not found.')
            sys.exit(1)

        self.copy_assets()

        self.ctx = {
            'sigal_link': sigal_link,
            'theme': {'name': os.path.basename(self.theme)},
            'medias': [],
            'albums': [],
            'breadcrumb': ''
        }

    def copy_assets(self):
        """Copy the theme files in the output dir."""

        self.theme_path = os.path.join(self.output_dir, 'static')
        copy_tree(os.path.join(self.theme, 'static'), self.theme_path)

    def get_breadcrumb(self, paths, relpath):
        """Paths to upper directories (with titles and links)."""

        tmp_path = relpath
        breadcrumb = [((self.url_ext or '.'), paths[tmp_path]['title'])]

        while True:
            tmp_path = os.path.normpath(os.path.join(tmp_path, '..'))
            if tmp_path == '.':
                break

            url = os.path.relpath(tmp_path, relpath) + '/' + self.url_ext
            breadcrumb.append((url, paths[tmp_path]['title']))

        return reversed(breadcrumb)

    def generate_context(self, paths, relpath):
        """Generate the context dict for the given path."""

        path = os.path.normpath(os.path.join(self.output_dir, relpath))
        index_url = os.path.relpath(self.output_dir, path) + '/' + self.url_ext
        self.logger.info("Output path : %s", path)

        ctx = copy.deepcopy(self.ctx)
        ctx.update({
            'settings': self.settings,
            'index_url': index_url,
            'index_title': paths['.']['title']
        })
        ctx['theme']['url'] = os.path.relpath(self.theme_path, path)

        if relpath != '.':
            ctx['breadcrumb'] = self.get_breadcrumb(paths, relpath)

        if len(paths[relpath]['medias']) > 0 and self.settings['zip_gallery']:
            ctx['zip_gallery'] = self.settings['zip_gallery']

        for i in paths[relpath]['medias']:
            media_ctx = {}
            base, ext = os.path.splitext(i)
            if ext in self.settings['img_ext_list']:
                media_ctx['type'] = 'img'
                media_ctx['file'] = i

                file_path = os.path.join(path, i)
                raw, simple = sigal.image.get_exif_tags(file_path)

                if raw is not None:
                    media_ctx['raw_exif'] = raw
                if simple is not None:
                    media_ctx['exif'] = simple
            else:
                media_ctx['type'] = 'vid'
                media_ctx['file'] = base + '.webm'
            media_ctx['thumb'] = get_thumb(self.settings, i)
            if self.settings['keep_orig']:
                media_ctx['big'] = get_orig(self.settings, i)
            ctx['medias'].append(media_ctx)

        for d in paths[relpath]['subdir']:
            dpath = os.path.normpath(os.path.join(relpath, d))
            alb_thumb = paths[dpath]['thumbnail']
            thumb_name = get_thumb(self.settings, alb_thumb)
            thumb_path = os.path.join(self.output_dir, dpath, thumb_name)
            self.logger.debug("Thumbnail path : %s", thumb_path)

            # generate the thumbnail if it is missing (if
            # settings['make_thumbs'] is False)
            if not os.path.exists(thumb_path):
                source = os.path.join(self.output_dir, dpath, alb_thumb)
                ext = os.path.splitext(source)[1]
                self.logger.debug("Generating thumbnail for %s", source)

                if ext in self.settings['img_ext_list']:
                    generator = sigal.image.generate_thumbnail
                else:
                    generator = sigal.video.generate_thumbnail

                generator(source, thumb_path, self.settings['thumb_size'],
                          fit=self.settings['thumb_fit'])

            ctx['albums'].append({
                'url': d + '/' + self.url_ext,
                'title': paths[dpath]['title'],
                'thumb': os.path.join(d, thumb_name)
            })

        return ctx

    def write(self, paths, relpath):
        """Generate the HTML page and save it."""

        ctx = self.generate_context(paths, relpath)
        page = self.template.render(paths[relpath], **ctx)

        output_file = os.path.join(self.output_dir, relpath, self.output_file)
        with codecs.open(output_file, 'w', 'utf-8') as f:
            f.write(page)
