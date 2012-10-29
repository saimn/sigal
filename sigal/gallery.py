#! /usr/bin/env python2
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

import logging
import os

from clint.textui import progress
from shutil import copy2

from .image import Image, copy_exif

DESCRIPTION_FILE = "index.md"


class Gallery:
    "Prepare images"

    def __init__(self, settings, input_dir):
        self.settings = settings
        self.input_dir = os.path.abspath(input_dir)
        self.logger = logging.getLogger(__name__)

    def filelist(self):
        "get the list of directories with files of particular extensions"

        for dirpath, dirnames, filenames in os.walk(self.input_dir):
            # filelist = [os.path.normcase(f) for f in os.listdir(dir)]
            imglist = [os.path.join(dirpath, f) for f in filenames
                       if os.path.splitext(f)[1] in self.settings['fileextlist']]
            yield dirpath, dirnames, imglist

    def build(self, output_dir, force=False):
        "create image gallery"

        self.output_dir = os.path.abspath(output_dir)
        self.force = force

        if not os.path.isdir(self.output_dir):
            self.logger.info("Create output directory %s", self.output_dir)
            os.makedirs(self.output_dir)

        # loop on directories
        for dirpath, dirnames, imglist in self.filelist():
            self.logger.warning("%s - %i images",
                                os.path.relpath(dirpath, self.input_dir),
                                len(imglist))

            img_dir = dirpath.replace(self.input_dir, self.output_dir)

            if not os.path.isdir(img_dir):
                os.mkdir(img_dir)

            descfile = os.path.join(dirpath, DESCRIPTION_FILE)
            if os.path.isfile(descfile):
                copy2(descfile, img_dir)

            if len(imglist) != 0:
                self.process_dir(imglist, img_dir)

    def process_dir(self, imglist, img_dir):
        "prepare images for a directory"

        thumb_dir = os.path.join(img_dir, self.settings['thumb_dir'])
        if not os.path.isdir(thumb_dir):
            os.mkdir(thumb_dir)

        if self.settings['big_img']:
            bigimg_dir = os.path.join(img_dir,
                                      self.settings['bigimg_dir'])
            if not os.path.isdir(bigimg_dir):
                os.mkdir(bigimg_dir)

        # loop on images
        for f in progress.bar(imglist):
            filename = os.path.split(f)[1]

            im_name = os.path.join(img_dir, filename)

            if os.path.isfile(im_name) and not self.force:
                self.logger.info("%s exists - skipping", filename)
                continue

            self.logger.info(filename)
            img = Image(f)

            if self.settings['big_img']:
                img.save(os.path.join(bigimg_dir, filename),
                         quality=self.settings['jpg_quality'])

            img.resize(self.settings['img_size'])

            if self.settings['copyright']:
                img.add_copyright(self.settings['copyright'])

            img.save(im_name, quality=self.settings['jpg_quality'])

            if self.settings['make_thumbs']:
                thumb_name = os.path.join(thumb_dir,
                                          self.settings['thumb_prefix'] +
                                          filename)
                img.thumbnail(thumb_name, self.settings['thumb_size'],
                              fit=self.settings['thumb_fit'],
                              quality=self.settings['jpg_quality'])

            if self.settings['exif']:
                copy_exif(f, im_name)
