# -*- coding: utf-8 -*-

"""Plugin which adds a watermark to the image.

Settings:

- ``watermark``: path to the watermark image.
- ``watermark_position``: the watermark position (scale or tile)
- ``watermark_opacity``: the watermark opacity (0.0 to 1.0)

"""

## Original code: http://code.activestate.com/recipes/362879-watermark-with-pil/

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
    layer = Image.new('RGBA', im.size, (0,0,0,0))
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
    position = 'scale'
    opacity = 1
    if settings['watermark_position']:
        position = settings['watermark_position']
    if settings['watermark_opacity']:
        opacity = settings["watermark_opacity"]

    return watermark(img, mark, position, opacity)


def register(settings):
    if settings.get('watermark'):
        signals.img_resized.connect(add_watermark)
    else:
        logger.warning('Watermark image is not set')
