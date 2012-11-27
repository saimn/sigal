# -*- coding:utf-8 -*-

# Copyright (c) 2009-2012 - Simon Conseil

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
Prepare images: resize images, and create thumbnails with some options
(squared thumbs, ...).
"""

from __future__ import division

import logging
import os

from PIL import Image as PILImage
from PIL import ImageDraw, ImageOps


class Image:
    """ Image container

    resize, thumbnail, ...

    :param filename: path to an image

    """

    def __init__(self, filename):
        self.filename = filename
        self.imgname = os.path.split(filename)[1]
        self.img = PILImage.open(filename)

    def save(self, filename, quality=90):
        self.img.save(filename, quality=quality)

    def resize(self, size):
        """ Resize the image

        - check if the image format is portrait or landscape and adjust `size`.
        - compute the width and height ratio, and keep the min to resize the
          image inside the `size` box without distorting it.

        :param size: tuple with the (with, height) to resize

        """

        if self.img.size[0] > self.img.size[1]:
            newsize = size
        else:
            newsize = (size[1], size[0])

        wratio = newsize[0] / self.img.size[0]
        hratio = newsize[1] / self.img.size[1]
        ratio = min(wratio, hratio)
        newsize = (int(ratio * self.img.size[0]),
                   int(ratio * self.img.size[1]))

        if ratio < 1:
            self.img = self.img.resize(newsize, PILImage.ANTIALIAS)

    def add_copyright(self, text):
        "Add a copyright to the image"

        draw = ImageDraw.Draw(self.img)
        draw.text((5, self.img.size[1] - 15), '\xa9 ' + text)

    def thumbnail(self, filename, box, fit=True, quality=90):
        "Create a thumbnail image"

        if fit:
            self.img = ImageOps.fit(self.img, box, PILImage.ANTIALIAS)
        else:
            self.img.thumbnail(box, PILImage.ANTIALIAS)

        self.img.save(filename, quality=quality)


def copy_exif(srcfile, dstfile):
    "Copy the exif metadatas from src to dest images"

    logger = logging.getLogger(__name__)

    import pyexiv2

    src = pyexiv2.ImageMetadata(srcfile)
    dst = pyexiv2.ImageMetadata(dstfile)
    src.read()
    dst.read()
    try:
        src.copy(dst)
    except:
        logger.error("metadata not copied for %s.", srcfile)
        return
    dst.write()
