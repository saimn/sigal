# -*- coding:utf-8 -*-

import os

from sigal.gallery import Gallery
from sigal import init_plugins

CURRENT_DIR = os.path.dirname(__file__)


def test_plugins(settings, tmpdir, disconnect_signals):

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


def test_stream(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    if "sigal.plugins.stream" not in settings["plugins"]:
        settings['plugins'] += ["sigal.plugins.stream"]
    title = 'Stream unit test'
    nb_items = 3
    filename = 'stream-test.html'
    settings['stream_page'] = {'filename': filename,
                               'nb_items': nb_items,
                               'title': title}

    init_plugins(settings)
    gal = Gallery(settings)
    gal.build()

    out_html = os.path.join(settings['destination'], filename)
    assert os.path.isfile(out_html)

    with open(out_html) as stream_page:
        content = stream_page.read()
        assert title in content
        assert content.count('data-big') == nb_items
