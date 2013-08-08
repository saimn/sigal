# -*- coding:utf-8 -*-

# Copyright (c)      2013 - Christophe-Marie Duquesne

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
import subprocess
import os
import re
import shutil
import sigal.image


def vid_size(source):
    """Returns the dimensions of the video"""
    pattern = re.compile(r'Stream.*Video.* ([0-9]+)x([0-9]+)')
    p = subprocess.Popen(['ffmpeg', '-i', source],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    match = pattern.search(stderr)
    if match:
        x, y = int(match.groups()[0]), int(match.groups()[1])
    else:
        x = y = 0
    return (x, y)


def generate_video(source, outname, size, options={}):
    """Video processor

    :param source: path to an image
    :param outname: name of the generated video
    :param options: array of options passed to ffmpeg

    """
    # Don't transcode if source is in the required format and
    # has fitting datedimensions, copy instead.
    w_src, h_src = vid_size(source)
    w_dst, h_dst = size
    base, src_ext = os.path.splitext(source)
    base, dst_ext = os.path.splitext(outname)
    if dst_ext == src_ext and w_src <= w_dst and h_src <= w_dst:
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
    with open("/dev/null") as devnull:
        subprocess.call(['ffmpeg', '-i', source, '-y',
            '-crf', options.get('crf', '10'),
            '-b:v', options.get('bitrate', '1.6M'),
            '-qmin', options.get('qmin', '4'),
            '-qmax', options.get('qmax', '63')] +
            resize_opt + [outname],
            stderr=devnull)


def generate_thumbnail(source, outname, box, fit=True, options=None):
    "Create a thumbnail image"
    # 1) dump an image of the video
    tmpfile = outname + ".tmp.jpg"
    with open("/dev/null") as devnull:
        subprocess.call(['ffmpeg', '-i', source, '-an', '-r', '1',
            '-vframes', '1', '-y', tmpfile], stderr=devnull)
    # 2) use the generate_thumbnail function from sigal.image
    sigal.image.generate_thumbnail(tmpfile, outname, box, fit, options)
    # 3) remove the image
    os.unlink(tmpfile)
