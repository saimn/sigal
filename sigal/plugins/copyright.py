"""Plugin which add a copyright to the image.

Settings:

- ``copyright``: the copyright text.
- ``copyright_text_font``: the copyright text font - either system/user
  font-name or absolute path to font.ttf file.  If no font is specified, or
  specified font is not found, the default font is used.
- ``copyright_text_font_size``: the copyright text font-size. If no font is
  specified, this setting is ignored.
- ``copyright_text_color``: the copyright text color in a tuple (R, G, B)
  with decimal RGB code, e.g. ``(255, 255, 255)`` is white.
- ``copyright_text_position``: the copyright text position in 2 tuple (left,
  top).  By default text would be positioned at bottom-left corner.

"""

import logging
from PIL import ImageDraw
from PIL import ImageFont
from sigal import signals

logger = logging.getLogger(__name__)


def add_copyright(img, settings=None):
    logger.debug('Adding copyright to %r', img)
    draw = ImageDraw.Draw(img)
    text = settings['copyright']
    font = settings.get('copyright_text_font', None)
    font_size = settings.get('copyright_text_font_size', 10)
    assert font_size >= 0
    color = settings.get('copyright_text_color', (0, 0, 0))
    bottom_margin = 3   # bottom margin for text
    text_height = bottom_margin + 12    # default text height (of 15) for default font
    if font:
        try:
            font = ImageFont.truetype(font, font_size)
            text_height = font.getsize(text)[1] + bottom_margin
        except:     # load default font in case of any exception
            logger.debug("Exception: Couldn't locate font %s, using default font", font)
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()
    left, top = settings.get('copyright_text_position', (5, img.size[1] - text_height))
    draw.text((left, top), text, fill=color, font=font)
    return img


def register(settings):
    if settings.get('copyright'):
        signals.img_resized.connect(add_copyright)
    else:
        logger.warning('Copyright text is not set')
