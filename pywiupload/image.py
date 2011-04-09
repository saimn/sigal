#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# pywiUpload - Piwigo gallery generator
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
    "Prepare a gallery of images for Piwigo"

    def __init__(self, params):
        self.filepath = ""
        self.galname = ""
        self.params = params

    def getpath(self, pathname):
        "return abslolute path from params dict"
        return os.path.join(self.filepath, self.params[pathname]) \
                if self.params.has_key(pathname) else ""

    def create_gallery(self, path):
        "create image gallery"
        imglist = get_filelist(path, self.params['fileExtList'])
        print "Found %i images in %s" % (len(imglist), path)

        while self.galname == "":
            self.galname = raw_input('Enter gallery name: ')

        self.filepath = os.path.join(os.path.dirname(imglist[0]),
                                                     self.galname)

        print "Create output dir ..."
        try:
            os.makedirs(self.getpath('thumb_dir'))
        except OSError:
            pass

        if self.params['bigimg']:
            try:
                os.mkdir(self.getpath('bigimg_dir'))
            except OSError:
                pass

        return (self.galname, self.process_images(imglist))

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

        if self.params['copyright']:
            copyrightmsg = raw_input('Enter copyright message: ')
            copyrightmsg = '\xa9 ' + copyrightmsg

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

            if self.params['bigimg']:
                im.save(os.path.join(self.getpath('bigimg_dir'), filename),
                        quality=self.params['jpgquality'])
                out_bigimglist.append(os.path.join(self.getpath('bigimg_dir'),
                                                  filename))

            # resize image
            if im.size[0] > im.size[1]:
                im_size = (self.params['im_width'], self.params['im_height'])
            else:
                im_size = (self.params['im_height'], self.params['im_width'])
            im2 = im.resize(im_size, Image.ANTIALIAS)

            # create thumbnail
            if self.params['squarethumb']:
                if im.size[0] > im.size[1]:
                    offset = (im.size[0] - im.size[1])/2
                    box = (offset, 0, im.size[0]-offset, im.size[1])
                else:
                    offset = (im.size[1] - im.size[0])/2
                    box = (0, offset, im.size[0], im.size[1]-offset)

                im = im.crop(box)
                thumbsize = (self.params['thumb_width'],
                             self.params['thumb_width'])
            else:
                thumbsize = (self.params['thumb_width'],
                             self.params['thumb_height'])

            im.thumbnail(thumbsize, Image.ANTIALIAS)

            # copyright
            if self.params['copyright']:
                draw = ImageDraw.Draw(im2)
                draw.text((5, im2.size[1]-15), copyrightmsg)

            # save
            im.save(os.path.join(self.getpath('thumb_dir'),
                                 self.params['thumb_prefix']+filename),
                    quality=self.params['jpgquality'])
            im2.save(os.path.join(self.filepath, filename),
                     quality=self.params['jpgquality'])

            out_thumblist.append(os.path.join(self.getpath('thumb_dir'),
                                             self.params['thumb_prefix']+
                                             filename))
            out_imglist.append(os.path.join(self.filepath, filename))

            if self.params['exif']:
                self.process_exif(f, os.path.join(self.filepath, filename))

        return [out_imglist, out_thumblist, out_bigimglist]

    def process_exif(self, srcfile, dstfile):
        "copy exif metadatas from src to dest images"
        try:
            import pyexiv2
        except ImportError:
            self.params['exif'] = 0
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

