#!/usr/bin/env python2
# -*- coding:utf-8 -*-

"""render theme for sigal"""

import os
from distutils.dir_util import copy_tree
from jinja2 import Environment, PackageLoader
import sigal.image

DEFAULT_THEME = "default"
INDEX_PAGE = "index.html"
IGNORED_DIR = ['css', 'js', 'img']

class Theme():
    """ Generate html """

    def __init__(self, params, path, theme=DEFAULT_THEME, tpl=INDEX_PAGE):
        self.path = path
        self.bigimg = params.getint('sigal', 'big_img')
        self.bigimg_dir = params.get('sigal', 'bigimg_dir')
        self.thumb_dir = params.get('sigal', 'thumb_dir')
        self.thumb_prefix = params.get('sigal', 'thumb_prefix')
        self.fileExtList = params.get('sigal', 'fileExtList')

        if params.has_option('sigal', 'theme'):
            theme = params.get('sigal', 'theme')

        env = Environment(loader=PackageLoader('sigal',
                                               os.path.join('..', 'themes', theme)))
        self.theme_dir = os.path.join('themes', theme)
        self.template = env.get_template(tpl)

        self.meta = {}
        self.meta['title'] = params.get('album', 'title') \
                             if params.has_option('album', 'title') else ''
        self.meta['author'] = params.get('album', 'author') \
                              if params.has_option('album', 'author') else ''
        self.meta['description'] = params.get('album', 'description') \
                              if params.has_option('album', 'description') else ''


    def filelist(self):
        "get the list of directories with files of particular extensions"
        ignored = [self.thumb_dir, self.bigimg_dir] + IGNORED_DIR

        for dirpath, dirnames, filenames in os.walk(self.path):
            # filelist = [os.path.normcase(f) for f in os.listdir(dir)]
            if os.path.split(dirpath)[1] not in ignored:
                imglist = [f for f in filenames \
                           if os.path.splitext(f)[1] in self.fileExtList]
                dirlist = [d for d in dirnames if d not in ignored]
                yield dirpath, dirlist, imglist

    def find_representative(self, path):
        """ find the representative image for a given album/path
        at the moment, this is the first image found.
        """

        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) \
                 and os.path.splitext(f)[1] in self.fileExtList]
        return files[0]

    def render(self):

        copy_tree(os.path.abspath(self.theme_dir),
                  os.path.abspath(self.path))

        # loop on directories
        for dirpath, dirnames, imglist in self.filelist():

            theme = { 'path': os.path.relpath(self.path, dirpath) }

            images = []
            for i in imglist:
                image = {
                    'file': i,
                    'thumb': os.path.join(self.thumb_dir, self.thumb_prefix+i)
                    }
                images.append(image)
                # print image

            albums = []
            for d in dirnames:
                alb_thumb = self.find_representative(os.path.join(dirpath, d))
                album = {'path': os.path.join(d, INDEX_PAGE),
                         'name': d,
                         'thumb': os.path.join(d, self.thumb_dir,
                                               self.thumb_prefix+alb_thumb),
                         }
                albums.append(album)
                # print album

            page = self.template.render(self.meta,
                                        images=images,
                                        albums=albums, theme=theme)

            # save
            f = open(os.path.join(dirpath, INDEX_PAGE),"w")
            f.write(page)
            f.close()
