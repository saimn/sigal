# -*- coding:utf-8 -*-

# Copyright (c)      2013 - Christophe-Marie Duquesne
# Copyright (c)      2013 - Simon Conseil

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

from __future__ import with_statement

import logging
import os
import re
import shutil
import subprocess

from . import compat, image
from .settings import get_thumb


def call_subprocess(cmd):
    """Wrapper to call subprocess.Popen and return stdout & stderr."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if not compat.PY2:
        stderr = stderr.decode('utf8')
        stdout = stdout.decode('utf8')
    return p.returncode, stdout, stderr


def check_subprocess(cmd, error_msg=''):

    returncode, stdout, stderr = call_subprocess(cmd)

    if returncode:
        logger = logging.getLogger(__name__)
        logger.error(error_msg)
        logger.debug('STDOUT:\n %s', stdout)
        logger.debug('STDERR:\n %s', stderr)
        raise subprocess.CalledProcessError(returncode, cmd)


def video_size(source):
    """Returns the dimensions of the video."""

    ret, stdout, stderr = call_subprocess(['ffmpeg', '-i', source])
    pattern = re.compile(r'Stream.*Video.* ([0-9]+)x([0-9]+)')
    match = pattern.search(stderr)

    if match:
        x, y = int(match.groups()[0]), int(match.groups()[1])
    else:
        x = y = 0
    return x, y


def generate_video(source, outname, size, options=None):
    """Video processor

    :param source: path to a video
    :param outname: name of the generated video
    :param options: array of options passed to ffmpeg

    """
    logger = logging.getLogger(__name__)

    # Don't transcode if source is in the required format and
    # has fitting datedimensions, copy instead.
    w_src, h_src = video_size(source)
    w_dst, h_dst = size
    logger.debug('Video size: %i, %i -> %i, %i', w_src, h_src, w_dst, h_dst)

    base, src_ext = os.path.splitext(source)
    base, dst_ext = os.path.splitext(outname)
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
    cmd = ['ffmpeg', '-i', source, '-y']  # -y to overwrite output files
    if options is not None:
        cmd += options
    cmd += resize_opt + [outname]

    logger.debug('Processing video: %s', ' '.join(cmd))
    try:
        check_subprocess(cmd, error_msg='Failed to process ' + source)
    except subprocess.CalledProcessError:
        return


def generate_thumbnail(source, outname, box, fit=True, options=None):
    """Create a thumbnail image for the video source, based on ffmpeg."""

    # 1) dump an image of the video
    tmpfile = outname + ".tmp.jpg"
    try:
        check_subprocess(
            ['ffmpeg', '-i', source, '-an', '-r', '1',
             '-vframes', '1', '-y', tmpfile],
            error_msg='Failed to create a thumbnail for ' + source
        )
    except subprocess.CalledProcessError:
        return

    # 2) use the generate_thumbnail function from sigal.image
    image.generate_thumbnail(tmpfile, outname, box, fit, options)
    # 3) remove the image
    os.unlink(tmpfile)


def process_video(filepath, outpath, settings):
    """Process a video: resize, create thumbnail."""

    filename = os.path.split(filepath)[1]
    basename = os.path.splitext(filename)[0]
    outname = os.path.join(outpath, basename + '.webm')

    generate_video(filepath, outname, settings['video_size'],
                    options=settings['webm_options'])

    if settings['make_thumbs']:
        thumb_name = os.path.join(outpath, get_thumb(settings, filename))
        generate_thumbnail(
            outname, thumb_name, settings['thumb_size'],
            fit=settings['thumb_fit'], options=settings['jpg_options'])
