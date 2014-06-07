# -*- coding: utf-8 -*-

"""Plugin which add a copyright to the image.

Settings:

- ``copyright``: the copyright text.

TODO: Add more settings (font, size, ...)

"""

import logging
from PIL import ImageDraw
from sigal import signals

logger = logging.getLogger(__name__)


def add_copyright(img, settings=None):
    logger.debug('Adding copyright to %r', img)
    draw = ImageDraw.Draw(img)
    draw.text((5, img.size[1] - 15), settings['copyright'])
    return img


def register(settings):
    if settings.get('copyright'):
        signals.img_resized.connect(add_copyright)
    else:
        logger.warning('Copyright text is not set')
