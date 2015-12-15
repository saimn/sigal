# -*- coding:utf-8 -*-

# Copyright (c) 2009-2014 - Simon Conseil
# Copyright (c) 2015 - François D.

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
import PIL
import pilkit.processors
import sys
import warnings
import fractions

from copy import deepcopy
from datetime import datetime
from PIL.ExifTags import TAGS, GPSTAGS
from PIL import Image as PILImage
from PIL import ImageOps
from pilkit.processors import Transpose
from pilkit.utils import save_image

from . import compat, signals, utils
from .settings import get_thumb, Status


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

    if settings['use_orig'] or source.endswith('.gif'):
        utils.copy(source, outname, symlink=settings['orig_link'])
        return

    img = PILImage.open(source)
    original_format = img.format

    if settings['copy_exif_data'] and settings['autorotate_images']:
        logger.warning("The 'autorotate_images' and 'copy_exif_data' settings "
                       "are not compatible because Sigal can't save the "
                       "modified Orientation tag.")

    # Preserve EXIF data
    if settings['copy_exif_data'] and _has_exif_tags(img):
        if options is not None:
            options = deepcopy(options)
        else:
            options = {}
        options['exif'] = img.info['exif']

    # Rotate the img, and catch IOError when PIL fails to read EXIF
    if settings['autorotate_images']:
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

    # signal.send() does not work here as plugins can modify the image, so we
    # iterate other the receivers to call them with the image.
    for receiver in signals.img_resized.receivers_for(img):
        img = receiver(img, settings=settings)

    outformat = img.format or original_format or 'JPEG'
    logger.debug(u'Save resized image to {0} ({1})'.format(outname, outformat))
    save_image(img, outname, outformat, options=options, autoconvert=True)


def generate_thumbnail(source, outname, box, delay, fit=True, options=None):
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

    logger = logging.getLogger(__name__)
    logger.info('Processing %s', filepath)
    filename = os.path.split(filepath)[1]
    outname = os.path.join(outpath, filename)
    ext = os.path.splitext(filename)[1]

    if ext in ('.jpg', '.jpeg', '.JPG', '.JPEG'):
        options = settings['jpg_options']
    elif ext == '.png':
        options = {'optimize': True}
    else:
        options = {}

    try:
        generate_image(filepath, outname, settings, options=options)

        if settings['make_thumbs']:
            thumb_name = os.path.join(outpath, get_thumb(settings, filename))
            generate_thumbnail(outname, thumb_name, settings['thumb_size'],
                               settings['thumb_video_delay'],
                               fit=settings['thumb_fit'], options=options)
    except Exception as e:
        logger.info('Failed to process: %r', e)
        return Status.FAILURE

    return Status.SUCCESS


def get_size(file_path):
    """Return image size (width and height)."""
    try:
        im = PILImage.open(file_path)
    except (IOError, IndexError, TypeError, AttributeError) as e:
        logger = logging.getLogger(__name__)
        logger.error("Could not read size of %s due to %r", file_path, e)
    else:
        width, height = im.size
        return {
            'width': width,
            'height': height
        }


def get_exif_data(filename):
    """Return a dict with the raw EXIF data."""

    logger = logging.getLogger(__name__)

    if PIL.PILLOW_VERSION == '3.0.0':
        warnings.warn('Pillow 3.0.0 is broken with EXIF data, consider using '
                      'another version if you want to use EXIF data.')

    img = PILImage.open(filename)
    try:
        exif = img._getexif() or {}
    except ZeroDivisionError:
        logger.warning('Failed to read EXIF data.')
        return None

    data = {TAGS.get(tag, tag): value for tag, value in exif.items()}

    if 'GPSInfo' in data:
        try:
            data['GPSInfo'] = {GPSTAGS.get(tag, tag): value
                               for tag, value in data['GPSInfo'].items()}
        except AttributeError:
            logger = logging.getLogger(__name__)
            logger.info('Failed to get GPS Info')
            del data['GPSInfo']
    return data


def dms_to_degrees(v):
    """Convert degree/minute/second to decimal degrees."""

    d = float(v[0][0]) / float(v[0][1])
    m = float(v[1][0]) / float(v[1][1])
    s = float(v[2][0]) / float(v[2][1])
    return d + (m / 60.0) + (s / 3600.0)


def get_exif_tags(data):
    """Make a simplified version with common tags from raw EXIF data."""

    logger = logging.getLogger(__name__)
    simple = {}

    for tag in ('Model', 'Make', 'LensModel'):
        if tag in data:
            if isinstance(data[tag], tuple):
                simple[tag] = data[tag][0].strip()
            else:
                simple[tag] = data[tag].strip()

    if 'FNumber' in data:
        fnumber = data['FNumber']
        try:
            simple['fstop'] = float(fnumber[0]) / fnumber[1]
        except IndexError:
            # Pillow == 3.0
            simple['fstop'] = float(fnumber[0])
        except Exception:
            logger.debug('Skipped invalid FNumber: %r', fnumber, exc_info=True)

    if 'FocalLength' in data:
        focal = data['FocalLength']
        try:
            simple['focal'] = round(float(focal[0]) / focal[1])
        except IndexError:
            # Pillow == 3.0
            simple['focal'] = round(focal[0])
        except Exception:
            logger.debug('Skipped invalid FocalLength: %r', focal,
                         exc_info=True)

    if 'ExposureTime' in data:
        exptime = data['ExposureTime']
        if isinstance(exptime, tuple):
            try:
                simple['exposure'] = str(fractions.Fraction(exptime[0],
                                                            exptime[1]))
            except IndexError:
                # Pillow == 3.0
                simple['exposure'] = exptime[0]
        elif isinstance(exptime, int):
            simple['exposure'] = str(exptime)
        else:
            logger.info('Unknown format for ExposureTime: %r', exptime)

    if 'ISOSpeedRatings' in data:
        if isinstance(data['ISOSpeedRatings'], tuple):
            # Pillow == 3.0
            simple['iso'] = data['ISOSpeedRatings'][0]
        else:
            simple['iso'] = data['ISOSpeedRatings']

    if 'DateTimeOriginal' in data:
        try:
            # Remove null bytes at the end if necessary
            date = data['DateTimeOriginal'].rsplit('\x00')[0]
        except AttributeError:
            # Pillow == 3.0
            date = data['DateTimeOriginal'][0]

        try:
            simple['dateobj'] = datetime.strptime(date, '%Y:%m:%d %H:%M:%S')
            dt = simple['dateobj'].strftime('%A, %d. %B %Y')
            simple['datetime'] = dt.decode('utf8') if compat.PY2 else dt
        except (ValueError, TypeError) as e:
            logger.info(u'Could not parse DateTimeOriginal: %s', e)

    if 'GPSInfo' in data:
        info = data['GPSInfo']
        lat_info = info.get('GPSLatitude')
        lon_info = info.get('GPSLongitude')
        lat_ref_info = info.get('GPSLatitudeRef')
        lon_ref_info = info.get('GPSLongitudeRef')

        if lat_info and lon_info and lat_ref_info and lon_ref_info:
            try:
                lat = dms_to_degrees(lat_info)
                lon = dms_to_degrees(lon_info)
            except (ZeroDivisionError, ValueError):
                logger.info('Failed to read GPS info')
            else:
                simple['gps'] = {
                    'lat': - lat if lat_ref_info != 'N' else lat,
                    'lon': - lon if lon_ref_info != 'E' else lon,
                }

    return simple
