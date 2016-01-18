# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014 - Simon Conseil

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

import locale
import sys

PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    string_types = (str,)
    unichr = chr
    strxfrm = locale.strxfrm

    from http import server
    from urllib.parse import quote as url_quote
    import socketserver
    import pickle
else:
    text_type = unicode  # NOQA
    string_types = (str, unicode)  # NOQA
    unichr = unichr

    def strxfrm(s):
        return locale.strxfrm(s.encode('utf-8'))

    from urllib import quote as url_quote  # NOQA
    import SimpleHTTPServer as server  # NOQA
    import SocketServer as socketserver  # NOQA

    try:
        import cPickle as pickle
    except:
        import pickle


class UnicodeMixin(object):
    if not PY2:
        __str__ = lambda x: x.__unicode__()
    else:
        __str__ = lambda x: unicode(x).encode('utf-8')
