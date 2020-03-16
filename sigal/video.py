# Copyright (c)      2013 - Christophe-Marie Duquesne
# Copyright (c) 2013-2020 - Simon Conseil

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
import os
import re
import shutil
import subprocess
from os.path import splitext

from . import image, utils
from .settings import get_thumb, Status
from .utils import is_valid_html5_video


class SubprocessException(Exception):
    pass


def check_subprocess(cmd, source, outname):
    """Run the command to resize the video and remove the output file if the
    processing fails.

    """
    logger = logging.getLogger(__name__)
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    except KeyboardInterrupt:
        logger.debug('Process terminated, removing file %s', outname)
        if os.path.isfile(outname):
            os.remove(outname)
        raise

    if res.returncode:
        logger.debug('STDOUT:\n %s', res.stdout.decode('utf8'))
        logger.debug('STDERR:\n %s', res.stderr.decode('utf8'))
        if os.path.isfile(outname):
            logger.debug('Removing file %s', outname)
            os.remove(outname)
        raise SubprocessException('Failed to process ' + source)


def video_size(source, converter='ffmpeg'):
    """Returns the dimensions of the video."""

    res = subprocess.run([converter, '-i', source], stderr=subprocess.PIPE)
    stderr = res.stderr.decode('utf8')
    pattern = re.compile(r'Stream.*Video.* ([0-9]+)x([0-9]+)')
    match = pattern.search(stderr)
    rot_pattern = re.compile(r'rotate\s*:\s*-?(90|270)')
    rot_match = rot_pattern.search(stderr)

    if match:
        x, y = int(match.groups()[0]), int(match.groups()[1])
    else:
        x = y = 0
    if rot_match:
        x, y = y, x
    return x, y


def generate_video(source, outname, settings, options=None):
    """Video processor.

    :param source: path to a video
    :param outname: path to the generated video
    :param settings: settings dict
    :param options: array of options passed to ffmpeg

    """
    logger = logging.getLogger(__name__)

    # Don't transcode if source is in the required format and
    # has fitting datedimensions, copy instead.
    converter = settings['video_converter']
    w_src, h_src = video_size(source, converter=converter)
    w_dst, h_dst = settings['video_size']
    logger.debug('Video size: %i, %i -> %i, %i', w_src, h_src, w_dst, h_dst)

    base, src_ext = splitext(source)
    base, dst_ext = splitext(outname)
    if dst_ext == src_ext and w_src <= w_dst and h_src <= h_dst:
        logger.debug('Video is smaller than the max size, copying it instead')
        shutil.copy(source, outname)
        return

    # http://stackoverflow.com/questions/8218363/maintaining-ffmpeg-aspect-ratio
    # + I made a drawing on paper to figure this out
    if h_dst * w_src < h_src * w_dst:
        # biggest fitting dimension is height
        resize_opt = ['-vf', "scale=trunc(oh*a/2)*2:%i" % h_dst]
    else:
        # biggest fitting dimension is width
        resize_opt = ['-vf', "scale=%i:trunc(ow/a/2)*2" % w_dst]

    # do not resize if input dimensions are smaller than output dimensions
    if w_src <= w_dst and h_src <= h_dst:
        resize_opt = []

    # Encoding options improved, thanks to
    # http://ffmpeg.org/trac/ffmpeg/wiki/vpxEncodingGuide
    cmd = [converter, '-i', source, '-y']  # -y to overwrite output files
    if options is not None:
        cmd += options
    cmd += resize_opt + [outname]

    logger.debug('Processing video: %s', ' '.join(cmd))
    check_subprocess(cmd, source, outname)


def generate_thumbnail(source, outname, box, delay, fit=True, options=None,
                       converter='ffmpeg'):
    """Create a thumbnail image for the video source, based on ffmpeg."""

    logger = logging.getLogger(__name__)
    tmpfile = outname + ".tmp.jpg"

    # dump an image of the video
    cmd = [converter, '-i', source, '-an', '-r', '1',
           '-ss', delay, '-vframes', '1', '-y', tmpfile]
    logger.debug('Create thumbnail for video: %s', ' '.join(cmd))
    check_subprocess(cmd, source, outname)

    # use the generate_thumbnail function from sigal.image
    image.generate_thumbnail(tmpfile, outname, box, fit=fit, options=options)
    # remove the image
    os.unlink(tmpfile)


def process_video(filepath, outpath, settings):
    """Process a video: resize, create thumbnail."""

    logger = logging.getLogger(__name__)
    filename = os.path.split(filepath)[1]
    basename, ext = splitext(filename)

    try:
        if settings['use_orig'] and is_valid_html5_video(ext):
            outname = os.path.join(outpath, filename)
            utils.copy(filepath, outname, symlink=settings['orig_link'])
        else:
            valid_formats = ['mp4', 'webm']
            video_format = settings['video_format']

            if video_format not in valid_formats:
                logger.error('Invalid video_format. Please choose one of: %s',
                             valid_formats)
                raise ValueError

            outname = os.path.join(outpath, basename + '.' + video_format)
            generate_video(filepath, outname, settings,
                           options=settings.get(video_format + '_options'))
    except Exception:
        if logger.getEffectiveLevel() == logging.DEBUG:
            raise
        else:
            return Status.FAILURE

    if settings['make_thumbs']:
        thumb_name = os.path.join(outpath, get_thumb(settings, filename))
        try:
            generate_thumbnail(
                outname, thumb_name, settings['thumb_size'],
                settings['thumb_video_delay'], fit=settings['thumb_fit'],
                options=settings['jpg_options'],
                converter=settings['video_converter'])
        except Exception:
            if logger.getEffectiveLevel() == logging.DEBUG:
                raise
            else:
                return Status.FAILURE

    return Status.SUCCESS
