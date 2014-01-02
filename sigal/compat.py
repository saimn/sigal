# -*- coding: utf-8 -*-

import sys

PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    string_types = (str,)
    unichr = chr

    from http import server
    import socketserver
else:
    text_type = unicode  # NOQA
    string_types = (str, unicode)  # NOQA
    unichr = unichr

    import SimpleHTTPServer as server
    import SocketServer as socketserver
