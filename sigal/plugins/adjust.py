"""Plugin which adjust the image after resizing.

Based on pilkit's Adjust_ processor.

.. _Adjust: https://github.com/matthewwithanm/pilkit/blob/master/pilkit/processors/base.py#L19

Settings::

    adjust_options = {'color': 1.0,
                      'brightness': 1.0,
                      'contrast': 1.0,
                      'sharpness': 1.0}

"""

import logging
from sigal import signals
from pilkit.processors import Adjust

logger = logging.getLogger(__name__)


def adjust(img, settings=None):
    logger.debug('Adjust image %r', img)
    return Adjust(**settings['adjust_options']).process(img)


def register(settings):
    if settings.get('adjust_options'):
        signals.img_resized.connect(adjust)
    else:
        logger.warning('Adjust options are not set')
