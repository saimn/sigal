# -*- coding: utf-8 -*-

# Copyright (c) 2011-2014 - Simon Conseil

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

import codecs
import os
import shutil
from markdown import Markdown
from subprocess import Popen, PIPE

from . import compat


class Devnull(object):
    """'Black hole' for output that should not be printed"""

    def write(self, *_):
        pass

    def flush(self, *_):
        pass


def copy(src, dst, symlink=False):
    """Copy or symlink the file."""
    func = os.symlink if symlink else shutil.copy2
    if symlink and os.path.lexists(dst):
        os.remove(dst)
    func(src, dst)


def check_or_create_dir(path):
    "Create the directory if it does not exist"

    if not os.path.isdir(path):
        os.makedirs(path)


def url_from_path(path):
    """Transform path to url, converting backslashes to slashes if needed."""

    if os.sep == '/':
        return path
    else:
        return '/'.join(path.split(os.sep))


def read_markdown(filename):
    """Reads markdown file, converts output and fetches title and meta-data for further processing."""
    # Use utf-8-sig codec to remove BOM if it is present. This is only possible this way prior to feeding the text to the
    # markdown parser (which would also default to pure utf-8)
    with codecs.open(filename, 'r', 'utf-8-sig') as f:
        text = f.read()
    md = Markdown(extensions=['meta'], output_format='html5')
    html = md.convert(text)
    try:
        meta = md.Meta.copy()
    except (AttributeError):
        meta = None
    if meta:
        title = md.Meta.get('title', [''])[0]
    else:
        title = None
    return {'title': title, 'description': html, 'meta': meta}


def call_subprocess(cmd):
    """Wrapper to call ``subprocess.Popen`` and return stdout & stderr."""
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    if not compat.PY2:
        stderr = stderr.decode('utf8')
        stdout = stdout.decode('utf8')
    return p.returncode, stdout, stderr


class cached_property(object):
    '''Decorator for read-only properties evaluated only once.

    © 2011 Christopher Arndt, MIT License
    https://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties

    The value is cached in the '_cache' attribute of the object instance that
    has the property getter method wrapped by this decorator. The '_cache'
    attribute value is a dictionary which has a key for every property of the
    object which is wrapped by this decorator. Each entry in the cache is
    created only when the property is accessed for the first time and is a
    two-element tuple with the last computed property value and the last time
    it was updated in seconds since the epoch.

    '''

    def __call__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        try:
            value = inst._cache[self.__name__]
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = value
        return value
