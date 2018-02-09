# -*- coding:utf-8 -*-

import blinker
import os

from sigal.gallery import Gallery
from sigal import init_plugins, signals

CURRENT_DIR = os.path.dirname(__file__)


def test_plugins(settings, tmpdir):

    settings['destination'] = str(tmpdir)
    if "sigal.plugins.nomedia" not in settings["plugins"]:
        settings['plugins'] += ["sigal.plugins.nomedia"]
    if "sigal.plugins.media_page" not in settings["plugins"]:
        settings['plugins'] += ["sigal.plugins.media_page"]

    try:
        init_plugins(settings)
        gal = Gallery(settings)
        gal.build()
    finally:
        # Reset plugins
        for name in dir(signals):
            if not name.startswith('_'):
                try:
                    sig = getattr(signals, name)
                    if isinstance(sig, blinker.Signal):
                        sig.receivers.clear()
                except Exception:
                    pass

    out_html = os.path.join(settings['destination'],
                            'dir2', 'exo20101028-b-full.jpg.html')
    assert os.path.isfile(out_html)

    for path, dirs, files in os.walk(os.path.join(str(tmpdir), "nomedia")):
        assert "ignore" not in path

        for file in files:
            assert "ignore" not in file
