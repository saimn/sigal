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

def generate_video(source, outname, options=['-vf', 'scale=800:trunc(ow/a/2)*2']):
    # http://stackoverflow.com/questions/8218363/maintaining-ffmpeg-aspect-ratio
    """Video processor

    :param source: path to an image
    :param outname: name of the generated video
    :param options: array of options passed to ffmpeg

    """
    with open("/dev/null") as devnull:
        subprocess.call(['ffmpeg', '-i', source, '-y'] + options +
                [outname], stderr=devnull)

def generate_thumbnail(source, outname, options=['-vf', 'scale=80:trunc(ow/a/2)*2']):
    # http://stackoverflow.com/questions/8218363/maintaining-ffmpeg-aspect-ratio
    "Create a thumbnail image"
    with open("/dev/null") as devnull:
        subprocess.call(['ffmpeg', '-i', source, '-an', '-r', '1',
            '-vframes', '1', '-y'] + options + [outname], stderr=devnull)
