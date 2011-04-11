#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - Piwigo gallery generator
# Copyright (C) 2009-2011 Simon - saimon.org
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

"""Create a gallery of images.

Resize images, create thumbnails with some options (rename images, squared
thumbs, ...).
"""

import os
import Image
import ImageDraw
from utils import get_filelist


class Gallery:
    "Prepare a gallery of images"

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
        self.fileExtList = params.get('sigal', 'fileExtList')

    def getsize(self, string):
        size = [int(i) for i in string.split("x")]
        if size[1] > size[0]:
            size[0], size[1] = size[1], size[0]
        return tuple(size)

    def build(self, input_dir, output_dir):
        "create image gallery"
        imglist = get_filelist(input_dir, self.fileExtList)
        print "Found %i images in %s" % (len(imglist), input_dir)

        self.output_dir = output_dir
        self.bigimg_dir = os.path.join(self.output_dir, self.bigimg_dir)
        self.thumb_dir = os.path.join(self.output_dir, self.thumb_dir)

        print "Create output directories ..."
        try:
            os.makedirs(self.thumb_dir)
            if self.bigimg:
                os.mkdir(self.bigimg_dir)
        except OSError:
            pass

        if self.copyright:
            self.copyright = '\xa9 ' + self.copyright

        return self.process_images(imglist)

    def add_copyright(self, img):
        "add copyright to image"
        draw = ImageDraw.Draw(img)
        draw.text((5, img.size[1]-15), self.copyright)

    def process_images(self, imglist):
        "prepare images"
        imglist.sort()
        out_imglist = []
        out_thumblist = []
        out_bigimglist = []

        imrename = raw_input("Rename images ('name01.jpg') ? (y/[n]) ")
        if imrename == 'y':
            count = 1
            imgname = raw_input('Enter new image name: ')
            nfill = 2 if (len(imglist)<100) else 3

        # loop on images
        for f in imglist:
            filename = os.path.split(f)[1]
            im = Image.open(f)

            if imrename == 'y':
                filename = imgname+str(count).zfill(nfill)+'.jpg'
                print "%s > %s" % (os.path.split(f)[1], filename)
                count += 1
            else:
                print "%s" % filename

            if self.bigimg:
                im.save(os.path.join(self.bigimg_dir, filename),
                        quality=self.jpgquality)
                out_bigimglist.append(os.path.join(self.bigimg_dir, filename))

            # resize image
            if im.size[0] > im.size[1]:
                im2 = im.resize(self.imsize, Image.ANTIALIAS)
            else:
                im2 = im.resize([self.imsize[1], self.imsize[0]], Image.ANTIALIAS)

            # create thumbnail
            if self.square_thumb:
                if im.size[0] > im.size[1]:
                    offset = (im.size[0] - im.size[1])/2
                    box = (offset, 0, im.size[0]-offset, im.size[1])
                else:
                    offset = (im.size[1] - im.size[0])/2
                    box = (0, offset, im.size[0], im.size[1]-offset)

                im = im.crop(box)
                thumb_size = [self.thumb_size[0], self.thumb_size[0]]
            elif im.size[0] > im.size[1]:
                thumb_size = self.thumb_size
            else:
                thumb_size = [self.thumb_size[1], self.thumb_size[0]]

            im.thumbnail(thumb_size, Image.ANTIALIAS)

            if self.copyright:
                self.add_copyright(im2)

            # save
            im.save(os.path.join(self.thumb_dir, self.thumb_prefix+filename),
                    quality=self.jpgquality)
            im2.save(os.path.join(self.output_dir, filename),
                     quality=self.jpgquality)

            out_thumblist.append(os.path.join(self.thumb_dir,
                                             self.thumb_prefix+filename))
            out_imglist.append(os.path.join(self.output_dir, filename))

            if self.exif:
                self.process_exif(f, os.path.join(self.output_dir, filename))

        return [out_imglist, out_thumblist, out_bigimglist]

    def process_exif(self, srcfile, dstfile):
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

