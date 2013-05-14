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

import logging
import pilkit.processors
import sys

from PIL import Image as PILImage
from PIL import ImageDraw, ImageOps
from pilkit.processors import Transpose
from pilkit.utils import save_image


def generate_image(source, outname, size, format, options=None,
                   autoconvert=True, copyright_text='', method='ResizeToFit'):
    """Image processor, rotate and resize the image.

    :param source: path to an image
    :param options: dict with PIL options (quality, optimize, progressive)

    """

    logger = logging.getLogger(__name__)
    img = PILImage.open(source)
    original_format = img.format

    # Rotate the img, and catch IOError when PIL fails to read EXIF
    try:
        img = Transpose().process(img)
    except IOError:
        pass

    # Resize the image
    try:
        logger.debug('Processor: %s', method)
        processor_cls = getattr(pilkit.processors, method)
    except AttributeError as e:
        logger.error('Wrong processor name: %s', method)
        sys.exit()

    processor = processor_cls(*size, upscale=False)
    img = processor.process(img)

    if copyright_text:
        add_copyright(img, copyright_text)

    format = format or img.format or original_format or 'JPEG'
    logger.debug('Save resized image to {0} ({1})'.format(outname, format))
    save_image(img, outname, format, options=options, autoconvert=autoconvert)


def generate_thumbnail(source, outname, box, format, fit=True, options=None):
    "Create a thumbnail image"

    logger = logging.getLogger(__name__)
    img = PILImage.open(source)
    original_format = img.format

    if fit:
        img = ImageOps.fit(img, box, PILImage.ANTIALIAS)
    else:
        img.thumbnail(box, PILImage.ANTIALIAS)

    format = format or img.format or original_format or 'JPEG'
    logger.debug('Save thumnail image to {0} ({1})'.format(outname, format))
    save_image(img, outname, format, options=options, autoconvert=True)


def add_copyright(img, text):
    "Add a copyright to the image"

    draw = ImageDraw.Draw(img)
    draw.text((5, img.size[1] - 15), '\xa9 ' + text)
