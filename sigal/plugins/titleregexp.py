# Copyright 2022 - C.Sehrt

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

""" This plugin modifies titles of galleries by using regular-expressions and
simple character replacements.

Settings:

- ``titleregexp`` with the following keys:
    - ``regexp``, which is an array of dicts with 'search', 'replace' and 
        'count' keys
    - ``substitute``, which is an array of 2-element-arrays, of which the
        second element denotes the replacement of occurences of the first 
        element

Example::

    titleregexp = {
        'regexp' : [
            { 'search': r"^([0-9]*)-(.*)$", 'replace': r"\2 (\1)", 'count': 1 },
            { 'search': r"([a-z][a-z])([A-Z][a-z])", 'replace': r"\1 \2" }
            ],
        'substitute' : [ [ '_', ' ' ] ]
    }

"""

import logging
import os
import re

from sigal import signals

logger = logging.getLogger(__name__)
cfg = {}

def titleregexp(album):
    """Create a title by regexping name"""
    #logger.info("DEBUG: name=%s, path=%s, title=%s", album.name, album.path, album.title)
    #print(dir(album))

    cfg = album.settings.get('titleregexp')

    n = 0
    total = 0

    for r in cfg.get('regexp') :
        album.title, n = re.subn(r.get('search'), r.get('replace'), album.title, r.get('count', 0))
        total += n

        if n>0 :
            for s in r.get('substitute', []) :
                album.title = album.title.replace(s[0],s[1])
            if r.get('break','') != '' :
                break

    for r in cfg.get('substitute', []) :
        album.title = album.title.replace(r[0],r[1])

    if total > 0:
        logger.info("Fixing title to '%s'", album.title)


def register(settings):
    if settings.get('titleregexp'):
        signals.album_initialized.connect(titleregexp)
    else:
        logger.warning("'titleregexp' setting not available!")
