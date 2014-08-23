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
    # Use utf-8-sig codec to remove BOM if it is present
    with codecs.open(filename, 'r', 'utf-8-sig') as f:
        text = f.read()

    md = Markdown(extensions=['meta'], output_format='html5')
    html = md.convert(text)

    return {
        'title': md.Meta.get('title', [''])[0],
        'description': html,
        'meta': md.Meta.copy()
    }


def call_subprocess(cmd):
    """Wrapper to call ``subprocess.Popen`` and return stdout & stderr."""
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    if not compat.PY2:
        stderr = stderr.decode('utf8')
        stdout = stdout.decode('utf8')
    return p.returncode, stdout, stderr
