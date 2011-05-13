#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - simple static gallery generator
# Copyright (C) 2009-2011 - Simon C. (saimon.org)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; If not, see http://www.gnu.org/licenses/

"""
Prepare images: resize images, and create thumbnails with some options
(squared thumbs, ...).
"""

import os
import Image
import ImageDraw
from shutil import copy2

DESCRIPTION_FILE = "album_description"

class Gallery:
    "Prepare images"

    def __init__(self, params):
        self.imsize = self.getsize(params.get('sigal', 'img_size'))
        self.bigimg = params.getint('sigal', 'big_img')
        self.bigimg_dir = params.get('sigal', 'bigimg_dir')

        self.thumb_size = self.getsize(params.get('sigal', 'thumb_size'))
        self.thumb_dir = params.get('sigal', 'thumb_dir')
        self.thumb_prefix = params.get('sigal', 'thumb_prefix')
        self.square_thumb = params.getint('sigal', 'square_thumb')

        self.jpgquality = params.getint('sigal', 'jpg_quality')
        self.exif = params.getint('sigal', 'exif')
        self.copyright = params.get('sigal', 'copyright')
        self.fileExtList = params.get('sigal', 'fileExtList').split(',')

    def getsize(self, string):
        "split size string to a tuple of int"
        size = [int(i) for i in string.split("x")]
        if size[1] > size[0]:
            size[0], size[1] = size[1], size[0]
        return tuple(size)

    def filelist(self):
        "get the list of directories with files of particular extensions"
        for dirpath, dirnames, filenames in os.walk(self.input_dir):
            # filelist = [os.path.normcase(f) for f in os.listdir(dir)]
            imglist = [os.path.join(dirpath, f) for f in filenames \
                       if os.path.splitext(f)[1] in self.fileExtList]
            yield dirpath, dirnames, imglist

    def build(self, input_dir, output_dir, force=False):
        "create image gallery"

        self.input_dir = os.path.abspath(input_dir)
        self.output_dir = os.path.abspath(output_dir)
        self.force = force

        if not os.path.isdir(self.output_dir):
            print "Create output directory %s" % self.output_dir
            os.makedirs(self.output_dir)

        if self.copyright:
            self.copyright = '\xa9 ' + self.copyright

        # loop on directories
        for dirpath, dirnames, imglist in self.filelist():
            print ":: %s - %i images" % (dirpath, len(imglist))

            img_dir = dirpath.replace(self.input_dir, self.output_dir)

            if not os.path.isdir(img_dir):
                os.mkdir(img_dir)

            descfile = os.path.join(dirpath, DESCRIPTION_FILE)
            if os.path.isfile(descfile):
                copy2(descfile, img_dir)

            if len(imglist) != 0:
                thumb_dir = os.path.join(img_dir, self.thumb_dir)
                if not os.path.isdir(thumb_dir):
                    os.mkdir(thumb_dir)

                bigimg_dir = ''
                if self.bigimg:
                    bigimg_dir = os.path.join(img_dir, self.bigimg_dir)
                    if not os.path.isdir(bigimg_dir):
                        os.mkdir(bigimg_dir)

                self.process_dir(imglist, img_dir, thumb_dir, bigimg_dir=bigimg_dir)

    def process_dir(self, imglist, img_dir, thumb_dir, bigimg_dir=''):
        "prepare images for a directory"

        # loop on images
        for f in imglist:
            filename = os.path.split(f)[1]

            im_name = os.path.join(img_dir, filename)
            thumb_name = os.path.join(thumb_dir, self.thumb_prefix+filename)

            if os.path.isfile(im_name) and os.path.isfile(thumb_name) and \
               not self.force:
                print "%s exists - skipping" % filename
                continue

            print "%s" % filename
            im = Image.open(f)

            if self.bigimg:
                im.save(os.path.join(bigimg_dir, filename),
                        quality=self.jpgquality)

            # resize image
            if im.size[0] > im.size[1]:
                im_resized = im.resize(self.imsize, Image.ANTIALIAS)
            else:
                im_resized = im.resize([self.imsize[1], self.imsize[0]],
                                       Image.ANTIALIAS)

            if self.copyright:
                self.add_copyright(im_resized)

            # save
            im_resized.save(im_name, quality=self.jpgquality)

            # create thumbnail
            self.make_thumb(im, thumb_name)

            if self.exif:
                self.copy_exif(f, im_name)

    def make_thumb(self, img, thumb_name):
        "create thumbnail image for img"
        if self.square_thumb:
            if img.size[0] > img.size[1]:
                offset = (img.size[0] - img.size[1])/2
                box = (offset, 0, img.size[0]-offset, img.size[1])
            else:
                offset = (img.size[1] - img.size[0])/2
                box = (0, offset, img.size[0], img.size[1]-offset)

            img = img.crop(box)
            thumb_size = [self.thumb_size[0], self.thumb_size[0]]
        elif img.size[0] > img.size[1]:
            thumb_size = self.thumb_size
        else:
            thumb_size = [self.thumb_size[1], self.thumb_size[0]]

        img.thumbnail(thumb_size, Image.ANTIALIAS)
        img.save(thumb_name, quality=self.jpgquality)

    def add_copyright(self, img):
        "add copyright to image"
        draw = ImageDraw.Draw(img)
        draw.text((5, img.size[1]-15), self.copyright)

    def copy_exif(self, srcfile, dstfile):
        "copy exif metadatas from src to dest images"
        try:
            import pyexiv2
        except ImportError:
            self.exif = 0
            print "Error: install pyexiv2 module to use exif metadatas."
            return

        if pyexiv2.version_info[1] == 1:
            src = pyexiv2.Image(srcfile)
            dst = pyexiv2.Image(dstfile)
            src.readMetadata()
            dst.readMetadata()
            try:
                src.copyMetadataTo(dst)
            except:
                print "Error: metadata not copied for %s." % srcfile
                return
            dst.writeMetadata()
        else:
            src = pyexiv2.ImageMetadata(srcfile)
            dst = pyexiv2.ImageMetadata(dstfile)
            src.read()
            dst.read()
            try:
                src.copy(dst)
            except:
                print "Error: metadata not copied for %s." % srcfile
                return
            dst.write()

