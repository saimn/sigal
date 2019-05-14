# Copyright 2019 - Remi Ferrand

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

""" This plugin offers the ability to disable ZIP gallery generation on a per album
granularity.

To ignore a ZIP gallery generation for a particular album, put a ``.nozip_gallery`` file next to it in its parent
folder. Only the existence of this ``.nozip_gallery`` file is tested.
"""

import logging
import os
from sigal import signals

logger = logging.getLogger(__name__)

def nozip_galery_file(album, settings=None):
    """Filesystem based switch to disable ZIP generation for an Album"""
    nozipgallerypath = os.path.join(album.src_path, ".nozip_gallery")

    if os.path.isfile(nozipgallerypath):
        logger.info("Ignoring ZIP gallery generation for album '%s' because of present "
                    ".nozip_gallery file", album.name)

        album.disable_zip_gallery = True

def register(settings):
    signals.album_initialized.connect(nozip_galery_file)
