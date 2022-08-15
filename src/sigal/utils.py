# Copyright (c) 2011-2020 - Simon Conseil

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
import shutil
from functools import lru_cache
from urllib.parse import quote

from markdown import Markdown
from markupsafe import Markup

from sigal.settings import Status

logger = logging.getLogger(__name__)
MD = None
VIDEO_MIMES = {'.mp4': 'video/mp4', '.webm': 'video/webm', '.ogv': 'video/ogg'}


class Devnull:
    """'Black hole' for output that should not be printed"""

    def write(self, *_):
        pass

    def flush(self, *_):
        pass


def copy(src, dst, symlink=False, rellink=False):
    """Copy or symlink the file."""
    func = os.symlink if symlink else shutil.copy2
    if symlink and os.path.lexists(dst):
        os.remove(dst)
    if rellink:  # relative symlink from dst
        func(os.path.relpath(src, os.path.dirname(dst)), dst)
    else:
        try:
            func(src, dst)
        except PermissionError:
            # this can happen if the file is not writable, so we try to remove
            # it first
            os.remove(dst)
            func(src, dst)


def check_or_create_dir(path):
    "Create the directory if it does not exist"

    if not os.path.isdir(path):
        os.makedirs(path)


@lru_cache(maxsize=1024)
def get_mod_date(path):
    """Get modification date for a path, caching result with LRU cache."""
    return os.path.getmtime(path)


def url_from_path(path):
    """Transform path to url, converting backslashes to slashes if needed."""

    if os.sep != '/':
        path = '/'.join(path.split(os.sep))
    return quote(path)


def read_markdown(filename):
    """Reads markdown file, converts output and fetches title and meta-data for
    further processing.
    """
    global MD
    # Use utf-8-sig codec to remove BOM if it is present. This is only possible
    # this way prior to feeding the text to the markdown parser (which would
    # also default to pure utf-8)
    with open(filename, encoding='utf-8-sig') as f:
        text = f.read()

    if MD is None:
        MD = Markdown(
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.meta',
                'markdown.extensions.tables',
            ],
            output_format='html5',
        )
    else:
        MD.reset()
        # When https://github.com/Python-Markdown/markdown/pull/672
        # will be available, this can be removed.
        MD.Meta = {}

    # Mark HTML with Markup to prevent jinja2 autoescaping
    output = {'description': Markup(MD.convert(text))}

    try:
        meta = MD.Meta.copy()
    except AttributeError:
        pass
    else:
        output['meta'] = meta
        try:
            output['title'] = MD.Meta['title'][0]
        except KeyError:
            pass

    return output


def is_valid_html5_video(ext):
    """Checks if ext is a supported HTML5 video."""
    return ext in VIDEO_MIMES.keys()


def get_mime(ext):
    """Returns mime type for extension."""
    return VIDEO_MIMES[ext]


class raise_if_debug:
    def __init__(self):
        self.value = None

    def __enter__(self, *args):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            logger.info('Failed to process: %r', exc_value)
            if logger.getEffectiveLevel() == logging.DEBUG:
                # propagate the exception
                return False
            else:
                self.value = Status.FAILURE
        else:
            self.value = Status.SUCCESS

        # suppress the exception
        return True
