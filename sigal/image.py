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

# Additional copyright notice:
#
# Several lines of code concerning extraction of GPS data from EXIF tags where
# taken from a GitHub Gist by Eran Sandler at
#
#   https://gist.github.com/erans/983821
#
# and partially modified. The code in question is licensed under MIT license.

import logging
import os
import pilkit.processors
import sys

from copy import deepcopy
from datetime import datetime
from PIL.ExifTags import TAGS, GPSTAGS
from PIL import Image as PILImage
from PIL import ImageDraw, ImageOps
from pilkit.processors import Transpose, Adjust
from pilkit.utils import save_image

from . import compat
from .settings import get_thumb


def _has_exif_tags(img):
    return hasattr(img, 'info') and 'exif' in img.info


def generate_image(source, outname, settings, options=None):
    """Image processor, rotate and resize the image.

    :param source: path to an image
    :param outname: output filename
    :param settings: settings dict
    :param options: dict with PIL options (quality, optimize, progressive)

    """

    logger = logging.getLogger(__name__)
    img = PILImage.open(source)
    original_format = img.format

    # Preserve EXIF data
    if settings['copy_exif_data'] and _has_exif_tags(img):
        if options is not None:
            options = deepcopy(options)
        else:
            options = {}
        options['exif'] = img.info['exif']

    # Rotate the img, and catch IOError when PIL fails to read EXIF
    try:
        img = Transpose().process(img)
    except (IOError, IndexError):
        pass

    # Resize the image
    if settings['img_processor']:
        try:
            logger.debug('Processor: %s', settings['img_processor'])
            processor_cls = getattr(pilkit.processors,
                                    settings['img_processor'])
        except AttributeError:
            logger.error('Wrong processor name: %s', settings['img_processor'])
            sys.exit()

        processor = processor_cls(*settings['img_size'], upscale=False)
        img = processor.process(img)

    # Adjust the image after resizing
    img = Adjust(**settings['adjust_options']).process(img)

    if settings['copyright']:
        add_copyright(img, settings['copyright'])

    outformat = img.format or original_format or 'JPEG'
    logger.debug(u'Save resized image to {0} ({1})'.format(outname, outformat))
    save_image(img, outname, outformat, options=options, autoconvert=True)


def generate_thumbnail(source, outname, box, fit=True, options=None):
    """Create a thumbnail image."""

    logger = logging.getLogger(__name__)
    img = PILImage.open(source)
    original_format = img.format

    if fit:
        img = ImageOps.fit(img, box, PILImage.ANTIALIAS)
    else:
        img.thumbnail(box, PILImage.ANTIALIAS)

    outformat = img.format or original_format or 'JPEG'
    logger.debug(u'Save thumnail image: {0} ({1})'.format(outname, outformat))
    save_image(img, outname, outformat, options=options, autoconvert=True)


def process_image(filepath, outpath, settings):
    """Process one image: resize, create thumbnail."""

    filename = os.path.split(filepath)[1]
    outname = os.path.join(outpath, filename)
    ext = os.path.splitext(filename)[1]

    if ext in ('.jpg', '.jpeg', '.JPG', '.JPEG'):
        options = settings['jpg_options']
    elif ext == '.png':
        options = {'optimize': True}
    else:
        options = {}

    generate_image(filepath, outname, settings, options=options)

    if settings['make_thumbs']:
        thumb_name = os.path.join(outpath, get_thumb(settings, filename))
        generate_thumbnail(outname, thumb_name, settings['thumb_size'],
                           fit=settings['thumb_fit'], options=options)


def add_copyright(img, text):
    """Add a copyright to the image."""

    draw = ImageDraw.Draw(img)
    draw.text((5, img.size[1] - 15), '\xa9 ' + text)


def _get_exif_data(filename):
    """Return a dict with EXIF data."""

    img = PILImage.open(filename)
    exif = img._getexif() or {}
    data = dict((TAGS.get(t, t), v) for (t, v) in exif.items())

    if 'GPSInfo' in data:
        gps_data = {}

        for tag in data['GPSInfo']:
            gps_data[GPSTAGS.get(tag, tag)] = data['GPSInfo'][tag]

        data['GPSInfo'] = gps_data

    return data


def dms_to_degrees(v):
    """Convert degree/minute/second to decimal degrees."""

    d = float(v[0][0]) / float(v[0][1])
    m = float(v[1][0]) / float(v[1][1])
    s = float(v[2][0]) / float(v[2][1])
    return d + (m / 60.0) + (s / 3600.0)


def get_exif_tags(source):
    """Read EXIF tags from file @source and return a tuple of two dictionaries,
    the first one containing the raw EXIF data, the second one a simplified
    version with common tags."""

    logger = logging.getLogger(__name__)

    if os.path.splitext(source)[1].lower() not in ('.jpg', '.jpeg'):
        return (None, None)

    try:
        data = _get_exif_data(source)
    except (IOError, IndexError, TypeError, AttributeError):
        logger.warning(u'Could not read EXIF data from {0}'.format(source))
        return (None, None)

    simple = {}

    # Provide more accessible tags in the 'simple' key
    if 'FNumber' in data:
        fnumber = data['FNumber']
        simple['fstop'] = float(fnumber[0]) / fnumber[1]

    if 'FocalLength' in data:
        focal = data['FocalLength']
        simple['focal'] = round(float(focal[0]) / focal[1])

    if 'ExposureTime' in data:
        simple['exposure'] = '{0}/{1}'.format(*data['ExposureTime'])

    if 'ISOSpeedRatings' in data:
        simple['iso'] = data['ISOSpeedRatings']

    if 'DateTimeOriginal' in data:
        try:
            # Remove null bytes at the end if necessary
            date = data['DateTimeOriginal'].rsplit('\x00')[0]
            dt = datetime.strptime(date, '%Y:%m:%d %H:%M:%S')
            dt = dt.strftime('%A, %d. %B %Y')

            if compat.PY2:
                simple['datetime'] = dt.decode('utf8')
            else:
                simple['datetime'] = dt
        except (ValueError, TypeError) as e:
            msg = u'Could not parse DateTimeOriginal of %s: %s' % (source, e)
            logger.warning(msg)

    if 'GPSInfo' in data:
        info = data['GPSInfo']
        lat_info = info.get('GPSLatitude')
        lon_info = info.get('GPSLongitude')
        lat_ref_info = info.get('GPSLatitudeRef')
        lon_ref_info = info.get('GPSLongitudeRef')

        if lat_info and lon_info and lat_ref_info and lon_ref_info:
            lat = dms_to_degrees(lat_info)
            lon = dms_to_degrees(lon_info)

            if lat_ref_info != 'N':
                lat = 0 - lat

            if lon_ref_info != 'E':
                lon = 0 - lon

            simple['gps'] = {'lat': lat, 'lon': lon}

    return (data, simple)
