# -*- coding:utf-8 -*-

import os

from sigal.gallery import Gallery
from sigal import init_plugins

CURRENT_DIR = os.path.dirname(__file__)


def test_plugins(settings, tmpdir):

    settings['destination'] = str(tmpdir)
    if "sigal.plugins.nomedia" not in settings["plugins"]:
        settings['plugins'] += ["sigal.plugins.nomedia"]
    if "sigal.plugins.media_page" not in settings["plugins"]:
        settings['plugins'] += ["sigal.plugins.media_page"]

    init_plugins(settings)
    gal = Gallery(settings)
    gal.build()

    out_html = os.path.join(settings['destination'],
                            'dir2', 'exo20101028-b-full.jpg.html')
    assert os.path.isfile(out_html)

    for path, dirs, files in os.walk(os.path.join(str(tmpdir), "nomedia")):
        assert "ignore" not in path

        for file in files:
            assert "ignore" not in file
