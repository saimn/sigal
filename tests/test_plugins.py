import os

from sigal.gallery import Gallery
from sigal.utils import init_plugins

CURRENT_DIR = os.path.dirname(__file__)


def _build_with_plugin(
    settings, input_path, output_path, plugin, **additional_settings
):
    settings["source"] = os.path.join(settings["source"], input_path)
    settings["destination"] = str(output_path)
    settings["plugins"] = [plugin]
    settings.update(additional_settings)

    init_plugins(settings)
    gal = Gallery(settings, ncpu=1)
    gal.build()
    return gal


def test_media_page(settings, tmp_path, disconnect_signals):
    _build_with_plugin(
        settings, "dir2", tmp_path, "sigal.plugins.media_page", theme="colorbox"
    )
    assert (tmp_path / "KeckObservatory20071020.jpg.html").is_file()


def test_nomedia(settings, tmp_path, disconnect_signals):
    _build_with_plugin(settings, "nomedia", tmp_path, "sigal.plugins.nomedia")

    for path, dirs, files in os.walk(str(tmp_path)):
        assert "ignore" not in path
        for file in files:
            assert "ignore" not in file


def test_nonmedia_files(settings, tmp_path, disconnect_signals):
    _build_with_plugin(
        settings,
        "nonmedia_files",
        tmp_path,
        "sigal.plugins.nonmedia_files",
        nonmedia_files_options={"thumb_bg_color": "red"},
    )
    assert (tmp_path / "dummy.pdf").is_file()
    assert (tmp_path / "thumbnails" / "dummy.tn.jpg").is_file()


def test_titleregexp(settings, tmp_path, disconnect_signals):
    conf = {
        "regexp": [
            {
                "search": r"test ?(.*)",
                "replace": r"titleregexp \1",
                "substitute": [["2", "02"]],
                "break": 1,
            }
        ]
    }
    gal = _build_with_plugin(
        settings, "dir1", tmp_path, "sigal.plugins.titleregexp", titleregexp=conf
    )
    assert gal.albums["test2"].title == "titleregexp 02"
