# -*- coding: utf-8 -*-

# Copyright (c) 2005 - Shane Hathaway (http://code.activestate.com/recipes/362879-watermark-with-pil/)
# Copyright (c) 2015 - Abdul Qabiz

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

"""Plugin which adds a watermark to the image.

Settings:

- ``watermark``: path to the watermark image.
- ``watermark_position``: the watermark position either 'scale' or 'tile' or
                          a 2-tuple giving the upper left corner, or
                          a 4-tuple defining the left, upper, right, and lower pixel coordinate, or
                          `None` (same as (0, 0)).
                          If a 4-tuple is given, the size of the pasted image must match the size of the region.
- ``watermark_opacity``: the watermark opacity (0.0 to 1.0).

"""


import logging
from PIL import ImageDraw, Image, ImageEnhance
from sigal import signals

logger = logging.getLogger(__name__)


def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im


def watermark(im, mark, position, opacity=1):
    """Adds a watermark to an image."""
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    # create a transparent layer the size of the image and draw the
    # watermark in that layer.
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    if position == 'tile':
        for y in range(0, im.size[1], mark.size[1]):
            for x in range(0, im.size[0], mark.size[0]):
                layer.paste(mark, (x, y))
    elif position == 'scale':
        # scale, but preserve the aspect ratio
        ratio = min(
            float(im.size[0]) / mark.size[0], float(im.size[1]) / mark.size[1])
        w = int(mark.size[0] * ratio)
        h = int(mark.size[1] * ratio)
        mark = mark.resize((w, h))
        layer.paste(mark, ((im.size[0] - w) / 2, (im.size[1] - h) / 2))
    else:
        layer.paste(mark, position)
    # composite the watermark with the layer
    return Image.composite(layer, im, layer)


def add_watermark(img, settings=None):
    logger.debug('Adding watermark to %r', img)
    mark = Image.open(settings['watermark'])
    position = settings.get('watermark_position', 'scale')
    opacity = settings.get("watermark_opacity", 1)
    return watermark(img, mark, position, opacity)


def register(settings):
    if settings.get('watermark'):
        signals.img_resized.connect(add_watermark)
    else:
        logger.warning('Watermark image is not set')
