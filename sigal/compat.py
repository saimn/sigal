# -*- coding: utf-8 -*-

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
else:
    text_type = unicode  # NOQA
    string_types = (str, unicode)  # NOQA
    unichr = unichr

    def strxfrm(s):
        return locale.strxfrm(s.encode('utf-8'))

    from urllib import quote as url_quote
    import SimpleHTTPServer as server
    import SocketServer as socketserver


class UnicodeMixin(object):
    if not PY2:
        __str__ = lambda x: x.__unicode__()
    else:
        __str__ = lambda x: unicode(x).encode('utf-8')
