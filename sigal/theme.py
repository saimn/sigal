#!/usr/bin/env python2
# -*- coding:utf-8 -*-

"""render theme for sigal"""

import os
from distutils.dir_util import copy_tree
from jinja2 import Environment, PackageLoader
import sigal.image

DEFAULT_THEME = "default"
INDEX_PAGE = "index.html"

class Theme():
    """ Generate html """

    def __init__(self, params, path, theme=DEFAULT_THEME, tpl=INDEX_PAGE):
        self.path = path
        self.bigimg = params.getint('sigal', 'big_img')
        self.bigimg_dir = params.get('sigal', 'bigimg_dir')
        self.thumb_dir = params.get('sigal', 'thumb_dir')
        self.thumb_prefix = params.get('sigal', 'thumb_prefix')
        self.fileExtList = params.get('sigal', 'fileExtList')

        env = Environment(loader=PackageLoader('sigal',
                                               os.path.join('..', 'themes', theme)))
        self.theme_dir = os.path.join('themes', theme)
        self.template = env.get_template(tpl)


    def filelist(self):
        "get the list of directories with files of particular extensions"
        ignored_dir = [self.thumb_dir, self.bigimg_dir, 'css']

        for dirpath, dirnames, filenames in os.walk(self.path):
            # filelist = [os.path.normcase(f) for f in os.listdir(dir)]
            if os.path.split(dirpath)[1] not in ignored_dir:
                imglist = [f for f in filenames \
                           if os.path.splitext(f)[1] in self.fileExtList]
                dirlist = [d for d in dirnames if d not in ignored_dir]
                yield dirpath, dirlist, imglist

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
                album = {'path': d+"/"+INDEX_PAGE,
                         'name': d
                         }
                albums.append(album)
                # print album

            page = self.template.render(title=dirpath, images=images,
                                        albums=albums, theme=theme)

            # save
            f = open(dirpath+"/"+INDEX_PAGE,"w")
            f.write(page)
            f.close()
