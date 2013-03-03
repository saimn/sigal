# -*- coding:utf-8 -*-

# Copyright (c) 2009-2013 - Simon Conseil

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

from __future__ import division

import logging
import os
import sys
from exceptions import IOError
from PIL import Image as PILImage
from PIL import ImageDraw, ImageOps, ImageFile

# EXIF specs Orientation constant
EXIF_ORIENTATION_TAG = 274


class Image(object):
    """Image container

    Prepare images: resize images, and create thumbnails with some options
    (squared thumbs, ...).

    :param filename: path to an image

    """

    def __init__(self, filename):
        self.filename = filename
        self.imgname = os.path.split(filename)[1]
        self.logger = logging.getLogger(__name__)

        with open(filename, 'rb') as fp:
            self.img = PILImage.open(fp)
            self.img.load()

        exif = self.img._getexif()
        if exif:
            # see: http://www.impulseadventure.com/photo/exif-orientation.html
            orientation = exif.get(EXIF_ORIENTATION_TAG)
            rotate_map = {3: 180, 6: -90, 8: 90}
            rotation = rotate_map.get(orientation)
            if rotation:
                self.img = self.img.rotate(rotation)

    def save(self, filename, **kwargs):
        """Save the image.

        Pass a dict with PIL options (quality, optimize, progressive). PIL can
        have problems saving large JPEGs if MAXBLOCK isn't big enough, So if
        we have a problem saving, we temporarily increase it. See
        http://github.com/jdriscoll/django-imagekit/issues/91

        """
        try:
            with quiet():
                self.img.save(filename, "JPEG", **kwargs)
        except IOError:
            old_maxblock = ImageFile.MAXBLOCK
            ImageFile.MAXBLOCK = self.img.size[0] * self.img.size[1]
            try:
                self.img.save(filename, "JPEG", **kwargs)
            finally:
                ImageFile.MAXBLOCK = old_maxblock

    def resize(self, size):
        """Resize the image.

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


class quiet(object):
    """A context manager for suppressing the stderr activity of PIL's C
    libraries. Based on http://stackoverflow.com/a/978264/155370

    """
    def __enter__(self):
        self.stderr_fd = sys.__stderr__.fileno()
        self.null_fd = os.open(os.devnull, os.O_RDWR)
        self.old = os.dup(self.stderr_fd)
        os.dup2(self.null_fd, self.stderr_fd)

    def __exit__(self, *args, **kwargs):
        os.dup2(self.old, self.stderr_fd)
        os.close(self.null_fd)
        os.close(self.old)
