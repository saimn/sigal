# -*- coding:utf-8 -*-

import os

from sigal.gallery import Gallery
from sigal import init_plugins

CURRENT_DIR = os.path.dirname(__file__)

def test_nomedia_plugin(settings, tmpdir):

    settings['destination'] = str(tmpdir)
    if "plugins"in settings:
        if not "sigal.plugins.nomedia" in settings["plugins"]:
            settings['plugins'] += ["sigal.plugins.nomedia"]
    else:
        settings["plugins"] = ["sigal.plugins.nomedia"]

    init_plugins(settings)
    gal = Gallery(settings)
    gal.build()

    for path, dirs, files in os.walk(os.path.join(str(tmpdir), "nomedia")):
        assert "ignore" not in path

        for file in files:
            assert "ignore" not in file