# -*- coding: utf-8 -*-

# Copyright (c) 2009-2014 - Simon Conseil
# Copyright (c)      2013 - Christophe-Marie Duquesne
# Copyright (c)      2014 - Jamie Starke

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

import os

"""Plugin which generates pages for each image.
"""

import logging
from sigal import signals
from sigal.writer import Writer

import codecs
from sigal.utils import check_or_create_dir
from sigal.utils import url_from_path
from sigal.pkgmeta import __url__ as sigal_link

logger = logging.getLogger(__name__)

class PageWriter(Writer):
    '''A writer for writing media pages, based on writer'''
    def __init__(self, settings, index_title=""):
        super(PageWriter, self).__init__(
            settings, index_title=index_title, template_file="media.html")

    def write(self, album, media_group):
        ''' Generate the media page and save it '''

        file_path = os.path.join(album.dst_path, media_group[0].filename)

        page = self.template.render({
            'album': album,
            'media': media_group[0],
            'previous_media': media_group[-1],
            'next_media': media_group[1],
            'index_title': self.index_title,
            'settings': self.settings,
            'sigal_link': sigal_link,
            'theme': {'name': os.path.basename(self.theme),
                      'url': url_from_path(os.path.relpath(self.theme_path,
                                                           file_path))},
        })

        output_file = "%s.html" % file_path

        with codecs.open(output_file, 'w', 'utf-8') as f:
            f.write(page)

def generate_media_pages(gallery):
    '''Generates and writes the media pages for all media in the gallery'''

    writer = PageWriter(gallery.settings,index_title=gallery.title)

    for album in gallery.albums.values():

        medias = album.medias
        next_medias = medias[1:] + [None]
        previous_medias = [None] + medias[:-1]

        # The media group allows us to easily get next and previous links
        media_groups = zip(medias, next_medias, previous_medias)

        for media_group in media_groups:
            writer.write(album,media_group)

    filenames = [os.path.join(album.dst_path, media.filename)
                    for album in gallery.albums.values()
                    for media in album.medias]

def register(settings):
    signals.gallery_build.connect(generate_media_pages)
