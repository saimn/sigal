import os

from sigal import init_plugins
from sigal.gallery import Gallery

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

    out_html = os.path.join(
        settings['destination'], 'dir2', 'KeckObservatory20071020.jpg.html'
    )
    assert os.path.isfile(out_html)

    for path, dirs, files in os.walk(os.path.join(str(tmpdir), "nomedia")):
        assert "ignore" not in path

        for file in files:
            assert "ignore" not in file


def test_nonmedia_files(settings, tmpdir, disconnect_signals):
    settings['destination'] = str(tmpdir)
    settings['plugins'] += ['sigal.plugins.nonmedia_files']
    settings['nonmedia_files_options'] = {'thumb_bg_color': 'red'}

    init_plugins(settings)

    gal = Gallery(settings)
    gal.build()

    outfile = os.path.join(settings['destination'], 'nonmedia_files', 'dummy.pdf')
    assert os.path.isfile(outfile)

    outthumb = os.path.join(
        settings['destination'], 'nonmedia_files', 'thumbnails', 'dummy.tn.jpg'
    )
    assert os.path.isfile(outthumb)


def test_titleregexp(settings, tmpdir, disconnect_signals):
    if "sigal.plugins.titleregexp" not in settings["plugins"]:
        settings['plugins'] += ["sigal.plugins.titleregexp"]

    init_plugins(settings)
    gal = Gallery(settings)
    gal.build()

    assert gal.albums.get('dir1').albums[1].title == "titleregexp 02"
