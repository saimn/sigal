# Copyright (c) 2009-2020 - Simon Conseil
# Copyright (c) 2015 - François D.
# Copyright (c) 2018 - Edwin Steele

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

import fractions
import logging
import os
import sys
import warnings
from copy import deepcopy
from datetime import datetime

import pilkit.processors
from PIL import Image as PILImage
from PIL import ImageFile, ImageOps, IptcImagePlugin
from PIL.ExifTags import GPSTAGS, TAGS
from pilkit.processors import Transpose
from pilkit.utils import save_image

from . import signals, utils
from .settings import Status, get_thumb

# Force loading of truncated files
ImageFile.LOAD_TRUNCATED_IMAGES = True


def _has_exif_tags(img):
    return hasattr(img, 'info') and 'exif' in img.info


def _read_image(file_path):
    # The image is already opened
    if isinstance(file_path, PILImage.Image):
        return file_path

    with warnings.catch_warnings(record=True) as caught_warnings:
        im = PILImage.open(file_path)

    for warning in caught_warnings:
        if warning.category == PILImage.DecompressionBombWarning:
            logger = logging.getLogger(__name__)
            logger.info('PILImage reported a possible DecompressionBomb'
                        ' for file {}'.format(file_path))
        else:
            warnings.showwarning(warning.message, warning.category,
                                 warning.filename, warning.lineno)
    return im


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

    img = _read_image(source)
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
        except (OSError, IndexError):
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

        width, height = settings['img_size']

        if img.size[0] < img.size[1]:
            # swap target size if image is in portrait mode
            height, width = width, height

        processor = processor_cls(width, height, upscale=False)
        img = processor.process(img)

    # signal.send() does not work here as plugins can modify the image, so we
    # iterate other the receivers to call them with the image.
    for receiver in signals.img_resized.receivers_for(img):
        img = receiver(img, settings=settings)

    # first, use hard-coded output format, or PIL format, or original image
    # format, or fall back to JPEG
    outformat = settings.get('img_format') or img.format or original_format or 'JPEG'
    logger.debug('Save resized image to %s (%s)', outname, outformat)
    save_image(img, outname, outformat, options=options, autoconvert=True)


def generate_thumbnail(source, outname, box, fit=True, options=None,
                       thumb_fit_centering=(0.5, 0.5)):
    """Create a thumbnail image."""

    logger = logging.getLogger(__name__)
    img = _read_image(source)
    original_format = img.format

    if fit:
        img = ImageOps.fit(img, box, PILImage.ANTIALIAS,
                           centering=thumb_fit_centering)
    else:
        img.thumbnail(box, PILImage.ANTIALIAS)

    outformat = img.format or original_format or 'JPEG'
    logger.debug('Save thumnail image: %s (%s)', outname, outformat)
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
            generate_thumbnail(
                outname, thumb_name, settings['thumb_size'],
                fit=settings['thumb_fit'], options=options,
                thumb_fit_centering=settings["thumb_fit_centering"])
    except Exception as e:
        logger.info('Failed to process: %r', e)
        if logger.getEffectiveLevel() == logging.DEBUG:
            raise
        else:
            return Status.FAILURE

    return Status.SUCCESS


def get_size(file_path):
    """Return image size (width and height)."""
    try:
        im = _read_image(file_path)
    except (OSError, IndexError, TypeError, AttributeError) as e:
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

    img = _read_image(filename)

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


def get_iptc_data(filename):
    """Return a dict with the raw IPTC data."""

    logger = logging.getLogger(__name__)

    iptc_data = {}
    raw_iptc = {}

    # PILs IptcImagePlugin issues a SyntaxError in certain circumstances
    # with malformed metadata, see PIL/IptcImagePlugin.py", line 71.
    # ( https://github.com/python-pillow/Pillow/blob/9dd0348be2751beb2c617e32ff9985aa2f92ae5f/src/PIL/IptcImagePlugin.py#L71 )
    try:
        img = _read_image(filename)
        raw_iptc = IptcImagePlugin.getiptcinfo(img)
    except SyntaxError:
        logger.info('IPTC Error in %s', filename)

    # IPTC fields are catalogued in:
    # https://www.iptc.org/std/photometadata/specification/IPTC-PhotoMetadata
    # 2:05 is the IPTC title property
    if raw_iptc and (2, 5) in raw_iptc:
        iptc_data["title"] = raw_iptc[(2, 5)].decode('utf-8', errors='replace')

    # 2:120 is the IPTC description property
    if raw_iptc and (2, 120) in raw_iptc:
        iptc_data["description"] = raw_iptc[(2, 120)].decode('utf-8',
                                                             errors='replace')

    # 2:105 is the IPTC headline property
    if raw_iptc and (2, 105) in raw_iptc:
        iptc_data["headline"] = raw_iptc[(2, 105)].decode('utf-8',
                                                          errors='replace')

    return iptc_data


def get_image_metadata(filename):
    logger = logging.getLogger(__name__)
    try:
        img = _read_image(filename)
    except Exception as e:
        logger.error('Could not open image %s metadata: %s',
                     filename, e)

    exif = None
    iptc = None
    size = None

    try:
        exif = get_exif_data(img)
    except Exception as e:
        logger.warning('Could not read EXIF data from %s: %s',
                       filename, e)

    try:
        iptc = get_iptc_data(img)
    except Exception as e:
        logger.warning('Could not read IPTC data from %s: %s',
                       filename, e)

    try:
        size = get_size(img)
    except Exception as e:
        logger.warning('Could not read size from %s: %s',
                       filename, e)

    return {
            'exif': exif,
            'iptc': iptc,
            'size': size,
            }


def dms_to_degrees(v):
    """Convert degree/minute/second to decimal degrees."""

    d = float(v[0][0]) / float(v[0][1])
    m = float(v[1][0]) / float(v[1][1])
    s = float(v[2][0]) / float(v[2][1])
    return d + (m / 60.0) + (s / 3600.0)


def get_exif_tags(data, datetime_format='%c'):
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
        except Exception:
            logger.debug('Skipped invalid FNumber: %r', fnumber, exc_info=True)

    if 'FocalLength' in data:
        focal = data['FocalLength']
        try:
            simple['focal'] = round(float(focal[0]) / focal[1])
        except Exception:
            logger.debug('Skipped invalid FocalLength: %r', focal,
                         exc_info=True)

    if 'ExposureTime' in data:
        exptime = data['ExposureTime']
        if isinstance(exptime, tuple):
            try:
                simple['exposure'] = str(fractions.Fraction(exptime[0],
                                                            exptime[1]))
            except ZeroDivisionError:
                logger.info('Invalid ExposureTime: %r', exptime)
        elif isinstance(exptime, int):
            simple['exposure'] = str(exptime)
        else:
            logger.info('Unknown format for ExposureTime: %r', exptime)

    if data.get('ISOSpeedRatings'):
        simple['iso'] = data['ISOSpeedRatings']

    if 'DateTimeOriginal' in data:
        # Remove null bytes at the end if necessary
        date = data['DateTimeOriginal'].rsplit('\x00')[0]

        try:
            simple['dateobj'] = datetime.strptime(date, '%Y:%m:%d %H:%M:%S')
            simple['datetime'] = simple['dateobj'].strftime(datetime_format)
        except (ValueError, TypeError) as e:
            logger.info('Could not parse DateTimeOriginal: %s', e)

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
            except (ZeroDivisionError, ValueError, TypeError):
                logger.info('Failed to read GPS info')
            else:
                simple['gps'] = {
                    'lat': - lat if lat_ref_info != 'N' else lat,
                    'lon': - lon if lon_ref_info != 'E' else lon,
                }

    return simple
