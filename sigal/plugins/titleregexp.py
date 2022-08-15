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
simple string or character replacements. It is acting in two phases: First, all
regular-expression-based modifications are carried out, second, string/character
replacements are done.

The first phase may be interrupted if a match occurs by the 'break'-setting
individually per regular-expression part. Additionally, if a match occurs,
string/character replacements may be added.

The second phase is done even if the first phase had been interrupted.

Settings:

- ``titleregexp`` with the following keys:
    - ``regexp``, which is an array of dicts with 'search', 'replace', 'break'
      'substitute' and 'count' keys. All but 'break' and 'substitute' are the
      arguments for ``re.subn``, without given 'count' all matches are replaced.
      If 'break' is anything but an empty string, the rest of the
      ``regexp``-array is being skipped. The 'substitute'-key contains an array
      following the ``substitute`` format explained in the next sentence and
      does string-replacement if the regular-expression matched.
    - ``substitute``, which is an array of 2-element-arrays, of which the
      occurences of the first element will be replaced by the second element by
      the ``replace``-method of strings.

Example::

    titleregexp = {
        'regexp' : [
            { 'search': r"^([0-9]*)-(.*)$", 'replace': r"\\2 (\\1)", 'count': 1,
              'break': 1, substitute: [ ['ae','ä'] ] },
            { 'search': r"([a-z][a-z])([A-Z][a-z])", 'replace': r"\\1 \\2" }
            ],
        'substitute' : [ [ '_', ' ' ] ]
    }

"""

import logging
import re

from sigal import signals

logger = logging.getLogger(__name__)


def titleregexp(album):
    """Create a title by regexping name"""

    cfg = album.settings.get('titleregexp')
    n = 0
    total = 0
    album_title_org = album.title

    for r in cfg.get('regexp'):
        album.title, n = re.subn(
            r.get('search'), r.get('replace'), album.title, r.get('count', 0)
        )
        total += n

        if n > 0:
            for s in r.get('substitute', []):
                album.title = album.title.replace(s[0], s[1])
            if r.get('break', '') != '':
                break

    for r in cfg.get('substitute', []):
        album.title = album.title.replace(r[0], r[1])

    if total > 0:
        logger.info("Fixing title '%s' to '%s'", album_title_org, album.title)


def register(settings):
    if settings.get('titleregexp'):
        signals.album_initialized.connect(titleregexp)
    else:
        logger.warning("'titleregexp' setting not available!")
