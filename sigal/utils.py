# Copyright (c) 2011-2018 - Simon Conseil

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

import os
import shutil
from markdown import Markdown
from markupsafe import Markup

from urllib.parse import quote

VIDEO_MIMES = {'.mp4': 'video/mp4',
               '.webm': 'video/webm',
               '.ogv': 'video/ogg'}

MD = None


class Devnull(object):
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
    with open(filename, 'r', encoding='utf-8-sig') as f:
        text = f.read()

    if MD is None:
        MD = Markdown(extensions=['markdown.extensions.meta',
                                  'markdown.extensions.tables'],
                      output_format='html5')
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


class cached_property(object):
    """ A property that is only computed once per instance and then replaces
    itself with an ordinary attribute. Deleting the attribute resets the
    property.
    Source:
        https://github.com/pydanny/cached-property (BSD Licensed)
        https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76

    """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value
