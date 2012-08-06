#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - simple static gallery generator
# Copyright (C) 2009-2012 - Simon C. (saimon.org)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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

from PIL import Image as PILImage
from PIL import ImageDraw, ImageOps
from shutil import copy2

try:
    import pyexiv2
except ImportError:
    pass

DESCRIPTION_FILE = "album_description"


class Image:
    "Handle Images: resize, thumbnail, ..."

    def __init__(self, filename):
        self.filename = filename
        self.imgname = os.path.split(filename)[1]
        self.img = PILImage.open(filename)

    def save(self, filename, quality=90):
        self.img.save(filename, quality=quality)

    def resize(self, size):
        "resize image"

        if self.img.size[0] > self.img.size[1]:
            self.img = self.img.resize(size, PILImage.ANTIALIAS)
        else:
            self.img = self.img.resize([size[1], size[0]], PILImage.ANTIALIAS)

    def add_copyright(self, text):
        "add copyright to image"

        draw = ImageDraw.Draw(self.img)
        draw.text((5, self.img.size[1] - 15), '\xa9 ' + text)

    def thumbnail(self, filename, box, fit=True, quality=90):
        "Create a thumbnail image"

        if fit:
            self.img = ImageOps.fit(self.img, box, PILImage.ANTIALIAS)
        else:
            self.img.thumbnail(box, PILImage.ANTIALIAS)

        self.img.save(filename, quality=quality)


class Gallery:
    "Prepare images"

    def __init__(self, settings, input_dir):
        self.settings = settings
        self.input_dir = os.path.abspath(input_dir)

    def filelist(self):
        "get the list of directories with files of particular extensions"

        for dirpath, dirnames, filenames in os.walk(self.input_dir):
            # filelist = [os.path.normcase(f) for f in os.listdir(dir)]
            imglist = [os.path.join(dirpath, f) for f in filenames \
                       if os.path.splitext(f)[1] in self.settings['fileextlist']]
            yield dirpath, dirnames, imglist

    def build(self, output_dir, force=False):
        "create image gallery"

        self.output_dir = os.path.abspath(output_dir)
        self.force = force

        if not os.path.isdir(self.output_dir):
            print "Create output directory %s" % self.output_dir
            os.makedirs(self.output_dir)

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
                thumb_dir = os.path.join(img_dir, self.settings['thumb_dir'])
                if not os.path.isdir(thumb_dir):
                    os.mkdir(thumb_dir)

                bigimg_dir = ''
                if self.settings['big_img']:
                    bigimg_dir = os.path.join(img_dir,
                                              self.settings['bigimg_dir'])
                    if not os.path.isdir(bigimg_dir):
                        os.mkdir(bigimg_dir)

                self.process_dir(imglist, img_dir, thumb_dir,
                                 bigimg_dir=bigimg_dir)

    def process_dir(self, imglist, img_dir, thumb_dir, bigimg_dir=''):
        "prepare images for a directory"

        # loop on images
        for f in imglist:
            filename = os.path.split(f)[1]

            im_name = os.path.join(img_dir, filename)

            thumb_name = os.path.join(thumb_dir,
                                      self.settings['thumb_prefix'] + filename)

            if os.path.isfile(im_name) and os.path.isfile(thumb_name) and \
               not self.force:
                print "%s exists - skipping" % filename
                continue

            print "%s" % filename
            img = Image(f)

            if self.settings['big_img']:
                img.save(os.path.join(bigimg_dir, filename),
                         quality=self.settings['jpg_quality'])

            img.resize(self.settings['img_size'])

            if self.settings['copyright']:
                img.add_copyright(self.settings['copyright'])

            img.save(im_name, quality=self.settings['jpg_quality'])

            img.thumbnail(thumb_name, self.settings['thumb_size'],
                          fit=self.settings['thumb_fit'],
                          quality=self.settings['jpg_quality'])

            if self.settings['exif']:
                copy_exif(f, im_name)


def copy_exif(srcfile, dstfile):
    "copy the exif metadatas from src to dest images"

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
