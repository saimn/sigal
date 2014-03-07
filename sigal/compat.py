# -*- coding: utf-8 -*-

import locale
import sys

PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    string_types = (str,)
    unichr = chr

    from functools import cmp_to_key
    alpha_sort = {'key': cmp_to_key(locale.strcoll)}

    from http import server
    import socketserver
else:
    text_type = unicode  # NOQA
    string_types = (str, unicode)  # NOQA
    unichr = unichr
    alpha_sort = {'cmp': locale.strcoll}

    import SimpleHTTPServer as server
    import SocketServer as socketserver


class UnicodeMixin(object):
    if not PY2:
        __str__ = lambda x: x.__unicode__()
    else:
        __str__ = lambda x: unicode(x).encode('utf-8')
