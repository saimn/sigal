import datetime
import logging
import os
import re
import shutil
from os.path import join

import pytest
from PIL import Image as PILImage
from types import SimpleNamespace

from sigal.gallery import Album, Gallery, Image, Media, Video
from sigal.video import SubprocessException
from sigal.writer import AlbumListPageWriter, AlbumPageWriter

try:
    from pillow_heif import HeifImagePlugin  # noqa: F401

    HAS_HEIF = True
except ImportError:
    HAS_HEIF = False

CURRENT_DIR = os.path.dirname(__file__)

REF = {
    "dir1": {
        "title": "An example gallery",
        "name": "dir1",
        "thumbnail": "./dir1/test1/thumbnails/11.tn.jpg",
        "subdirs": ["test1", "test2", "test3"],
        "medias": [],
    },
    "dir1/test1": {
        "title": "An example sub-category",
        "name": "test1",
        "thumbnail": "./test1/thumbnails/11.tn.jpg",
        "subdirs": [],
        "medias": [
            "11.jpg",
            "CMB_Timeline300_no_WMAP.jpg",
            "flickr_jerquiaga_2394751088_cc-by-nc.jpg",
            "example.gif",
        ],
    },
    "dir1/test2": {
        "title": "test2",
        "name": "test2",
        "thumbnail": "./test2/thumbnails/21.tn.tiff",
        "subdirs": [],
        "medias": ["21.tiff", "22.jpg", "CMB_Timeline300_no_WMAP.jpg"],
    },
    "dir1/test3": {
        "title": "01 First title alphabetically",
        "name": "test3",
        "thumbnail": "./test3/thumbnails/3.tn.jpg",
        "subdirs": [],
        "medias": ["3.jpg"],
    },
    "dir2": {
        "title": "Another example gallery with a very long name",
        "name": "dir2",
        "thumbnail": "./dir2/thumbnails/m57_the_ring_nebula-587px.tn.jpg",
        "subdirs": [],
        "medias": [
            "KeckObservatory20071020.jpg",
            "Hubble Interacting Galaxy NGC 5257.jpg",
            "Hubble ultra deep field.jpg",
            "m57_the_ring_nebula-587px.jpg",
        ],
    },
    "accentué": {
        "title": "accentué",
        "name": "accentué",
        "thumbnail": "./accentu%C3%A9/thumbnails/h%C3%A9lico%C3%AFde.tn.jpg",
        "subdirs": [],
        "medias": ["hélicoïde.jpg", "11.jpg"],
    },
    "video": {
        "title": "video",
        "name": "video",
        "thumbnail": "./video/thumbnails/example%20video.tn.jpg",
        "subdirs": [],
        "medias": ["example video.ogv"],
    },
    "webp": {
        "title": "webp",
        "name": "webp",
        "thumbnail": "./webp/thumbnails/_MG_7805_lossy80.tn.webp",
        "subdirs": [],
        "medias": ["_MG_7805_lossy80.webp", "_MG_7808_lossy80.webp"],
    },
}


def test_media(settings):
    m = Media("11.jpg", "dir1/test1", settings)
    path = join("dir1", "test1")
    file_path = join(path, "11.jpg")
    thumb = join("thumbnails", "11.tn.jpg")

    assert m.dst_filename == "11.jpg"
    assert m.src_path == join(settings["source"], file_path)
    assert m.dst_path == join(settings["destination"], file_path)
    assert m.thumb_name == thumb
    assert m.thumb_path == join(settings["destination"], path, thumb)
    assert m.title == "Foo Bar"
    assert m.description.startswith(
        "<p>This is a <em>funny</em> <strong>description</strong> of this image</p>"
    )

    assert repr(m) == f"<Media>('{file_path}')"
    assert str(m) == file_path


def test_media_orig(settings, tmpdir):
    settings["keep_orig"] = False
    m = Media("11.jpg", "dir1/test1", settings)
    assert m.big is None

    settings["keep_orig"] = True
    settings["destination"] = str(tmpdir)

    m = Image("11.jpg", "dir1/test1", settings)
    assert m.big == "original/11.jpg"

    m = Video("example video.ogv", "video", settings)
    assert m.dst_filename == "example video.webm"
    assert m.big_url == "./original/example%20video.ogv"
    assert os.path.isfile(join(settings["destination"], m.path, m.big))

    settings["use_orig"] = True

    m = Image("21.jpg", "dir1/test2", settings)
    assert m.big == "21.jpg"


def test_media_iptc_override(settings):
    img_with_md = Image("2.jpg", "iptcTest", settings)
    assert img_with_md.title == "Markdown title beats iptc"
    # Markdown parsing adds formatting. Let's just focus on content
    assert "Markdown description beats iptc" in img_with_md.description
    img_no_md = Image("1.jpg", "iptcTest", settings)
    assert (
        img_no_md.title
        == "Haemostratulus clouds over Canberra - 2005-12-28 at 03-25-07"
    )
    assert (
        img_no_md.description == '"Haemo" because they look like haemoglobin '
        'cells and "stratulus" because I can\'t work out whether '
        "they're Stratus or Cumulus clouds.\nWe're driving down "
        "the main drag in Canberra so it's Parliament House that "
        "you can see at the end of the road."
    )


def test_media_img_format(settings):
    settings["img_format"] = "JPEG"
    m = Image("11.tiff", "dir1/test1", settings)
    path = join("dir1", "test1")
    thumb = join("thumbnails", "11.tn.jpg")

    assert m.dst_filename == "11.jpg"
    assert m.src_path == join(settings["source"], path, "11.tiff")
    assert m.dst_path == join(settings["destination"], path, "11.jpg")
    assert m.thumb_name == thumb
    assert m.thumb_path == join(settings["destination"], path, thumb)
    assert m.title == "Foo Bar"
    assert m.description.startswith(
        "<p>This is a <em>funny</em> <strong>description</strong> of this image</p>"
    )

    file_path = join(path, "11.tiff")
    assert repr(m) == f"<Image>('{file_path}')"
    assert str(m) == file_path


def test_image(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    settings["datetime_format"] = "%d/%m/%Y"
    m = Image("11.jpg", "dir1/test1", settings)
    assert m.date == datetime.datetime(2006, 1, 22, 10, 32, 42)
    assert m.exif["datetime"] == "22/01/2006"

    os.makedirs(join(settings["destination"], "dir1", "test1", "thumbnails"))
    assert m.thumbnail == join(".", "thumbnails", "11.tn.jpg")
    assert os.path.isfile(m.thumb_path)


def test_video(settings, tmpdir):
    settings["destination"] = str(tmpdir)
    m = Video("example video.ogv", "video", settings)

    src_path = join("video", "example video.ogv")
    assert str(m) == src_path

    file_path = join("video", "example video.webm")
    assert m.dst_path == join(settings["destination"], file_path)

    os.makedirs(join(settings["destination"], "video", "thumbnails"))
    assert m.thumbnail == join(".", "thumbnails", "example%20video.tn.jpg")
    assert os.path.isfile(m.thumb_path)


@pytest.mark.parametrize("path,album", REF.items())
def test_album(path, album, settings, tmpdir):
    gal = Gallery(settings, ncpu=1)
    a = Album(path, settings, album["subdirs"], album["medias"], gal)

    assert a.title == album["title"]
    assert a.name == album["name"]
    assert a.subdirs == album["subdirs"]
    assert a.thumbnail == album["thumbnail"]
    if path == "video":
        assert list(a.images) == []
        assert [m.dst_filename for m in a.medias] == [
            album["medias"][0].replace(".ogv", ".webm")
        ]
    else:
        assert list(a.videos) == []
        assert [m.dst_filename for m in a.medias] == album["medias"]
    assert len(a) == len(album["medias"])


def test_album_url_uses_output_filename(settings):
    gal = Gallery(settings, ncpu=1)
    album = Album("dir1", settings, ["test1"], [], gal)

    assert album.url == "dir1/index.html"


def test_build_with_multiprocessing(settings, tmp_path):
    settings["source"] = os.path.join(CURRENT_DIR, "sample", "pictures")
    settings["destination"] = str(tmp_path)
    settings["theme"] = "photobook"

    gal = Gallery(settings, ncpu=2)
    gal.build()

    assert os.path.isfile(os.path.join(settings["destination"], "index.html"))


def test_album_map_markers_and_route(settings):
    class FakeMedia:
        def __init__(self, path, thumb_name, gps, date, title):
            self.path = path
            self.thumb_name = thumb_name
            self.gps = gps
            self.date = date
            self.title = title

    gal = SimpleNamespace(albums={})
    album = Album("loc", settings, [], [], gal)
    album.medias = [
        FakeMedia("loc", "thumb1.jpg", {"lat": 1.0, "lon": 2.0}, datetime.datetime(2020, 1, 1), "First"),
        FakeMedia("loc", "thumb2.jpg", {"lat": 1.0, "lon": 2.0}, datetime.datetime(2020, 1, 2), "Second"),
        FakeMedia("loc", "thumb3.jpg", {"lat": 2.0, "lon": 3.0}, datetime.datetime(2020, 1, 3), "Third"),
    ]

    markers = album.map_markers
    assert len(markers) == 2
    assert markers[0]["lat"] == 1.0
    assert markers[0]["lon"] == 2.0
    assert markers[0]["items"][0]["caption"] == "First"
    assert markers[0]["items"][1]["caption"] == "Second"
    assert markers[1]["lat"] == 2.0
    assert markers[1]["items"][0]["caption"] == "Third"

    assert album.route == [{"lat": 1.0, "lon": 2.0}, {"lat": 2.0, "lon": 3.0}]


def test_map_template_uses_items_key_across_themes(settings, tmp_path):
    settings["destination"] = str(tmp_path)
    settings["show_map"] = True
    settings["map_height"] = "200px"
    settings["leaflet_provider"] = "OpenStreetMap"
    settings["datetime_format"] = "%Y-%m-%d"

    album = SimpleNamespace(
        show_map=True,
        map_markers=[
            {
                "lat": 1.0,
                "lon": 2.0,
                "url": "thumb1.jpg",
                "caption": "First",
                "datetime": "2020-01-01",
                "album_url": "./loc/index.html",
                "items": [
                    {
                        "thumbnail": "thumb1.jpg",
                        "caption": "First",
                        "datetime": "2020-01-01",
                        "album_url": "./loc/index.html",
                    }
                ],
            }
        ],
        route=[{"lat": 1.0, "lon": 2.0}],
    )

    for theme in ["colorbox", "photobook", "galleria", "photoswipe"]:
        settings["theme"] = theme
        writer = AlbumPageWriter(settings, index_title="Sigal test gallery")
        template = writer.template.environment.get_template("map.html")
        html = template.render(album=album, settings=settings)

        assert "items: [" in html
        assert 'caption: "First"' in html
        assert 'thumbnail: "thumb1.jpg"' in html


def test_photobook_theme_renders_trip_map_feature(settings, tmp_path):
    settings["destination"] = str(tmp_path)
    settings["theme"] = "photobook"
    settings["show_map"] = True
    settings["map_height"] = "200px"
    settings["leaflet_provider"] = "OpenStreetMap"

    album = SimpleNamespace(
        title="Test album",
        description="Test description",
        dst_path=str(tmp_path),
        index_url="./index.html",
        show_map=True,
        map_markers=[
            {
                "lat": 1.0,
                "lon": 2.0,
                "url": "thumb1.jpg",
                "caption": "First",
                "datetime": "2020-01-01",
                "album_url": "./loc/index.html",
                "items": [
                    {
                        "thumbnail": "thumb1.jpg",
                        "caption": "First",
                        "datetime": "2020-01-01",
                        "album_url": "./loc/index.html",
                    }
                ],
            }
        ],
        route=[{"lat": 1.0, "lon": 2.0}],
        medias=[],
    )

    writer = AlbumPageWriter(settings, index_title="Sigal test gallery")
    html = writer.template.render(**writer.generate_context(album))
    assert '<div id="mapid"' in html
    assert 'leaflet/leaflet.js' in html

    list_album = SimpleNamespace(
        title="Root album",
        description="",
        dst_path=str(tmp_path),
        index_url="index.html",
        show_map=True,
        map_markers=album.map_markers,
        route=album.route,
        albums=[
            SimpleNamespace(
                url="dir1/index.html",
                thumbnail="./dir1/thumbnails/11.tn.jpg",
                name="dir1",
                title="Dir1",
            )
        ],
    )

    list_writer = AlbumListPageWriter(settings, index_title="Sigal test gallery")
    list_html = list_writer.template.render(**list_writer.generate_context(list_album))
    assert '<div id="mapid"' in list_html


def test_photobook_theme_album_page_renders_map_with_sample_media(settings, tmp_path):
    from sigal.gallery import Image

    settings["destination"] = str(tmp_path)
    settings["theme"] = "photobook"
    settings["show_map"] = True
    settings["map_height"] = "200px"
    settings["leaflet_provider"] = "OpenStreetMap"

    gal = Gallery(settings, ncpu=1)
    album = Album("dir1/test1", settings, [], ["11.jpg"], gal)
    assert len(album.medias) == 1

    media = album.medias[0]
    media.exif = {
        "gps": {"lat": 48.8566, "lon": 2.3522},
        "dateobj": datetime.datetime(2020, 1, 1, 12, 0, 0),
        "datetime": "2020-01-01",
    }

    writer = AlbumPageWriter(settings, index_title="Sigal test gallery")
    html = writer.template.render(**writer.generate_context(album))

    assert '<div id="mapid"' in html
    assert "items: [" in html
    assert "L.map('mapid'" in html
    assert ".photoLayer" not in html or "photoLayer.add(photos).addTo(map);" in html


def test_breadcrumb_does_not_link_current_album(settings, tmp_path):
    settings["source"] = os.path.join(CURRENT_DIR, "sample", "pictures")
    settings["destination"] = str(tmp_path)
    settings["theme"] = "photoswipe"
    gal = Gallery(settings, ncpu=1)

    parent = Album("dir1", settings, [], [], gal)
    album = Album("dir1/test1", settings, [], [], gal)
    gal.albums = {"dir1": parent, "dir1/test1": album}

    writer = AlbumPageWriter(settings, index_title="Sigal test gallery")
    breadcrumb = writer.template.environment.get_template("breadcrumb.html")
    html = breadcrumb.render(album=album)

    assert '<span>An example sub-category</span>' in html
    assert 'href="index.html">An example sub-category</a>' not in html


def test_photobook_album_list_includes_root_description(settings, tmp_path):
    settings["source"] = os.path.join(CURRENT_DIR, "sample", "pictures")
    settings["destination"] = str(tmp_path)
    settings["theme"] = "photobook"
    gal = Gallery(settings, ncpu=1)

    root_album = Album(".", settings, ["dir1"], [], gal)
    child_album = Album("dir1", settings, [], [], gal)
    gal.albums = {".": root_album, "dir1": child_album}

    writer = AlbumListPageWriter(settings, index_title="Sigal test gallery")
    html = writer.template.render(**writer.generate_context(root_album))

    assert "This gallery was generated with" in html


def test_albums_sort(settings):
    gal = Gallery(settings, ncpu=1)
    album = REF["dir1"]
    subdirs = list(album["subdirs"])

    settings["albums_sort_reverse"] = False
    a = Album("dir1", settings, album["subdirs"], album["medias"], gal)
    a.sort_subdirs("")
    assert [alb.name for alb in a.albums] == subdirs

    settings["albums_sort_reverse"] = True
    a = Album("dir1", settings, album["subdirs"], album["medias"], gal)
    a.sort_subdirs("")
    assert [alb.name for alb in a.albums] == list(reversed(subdirs))

    titles = [im.title for im in a.albums]
    titles.sort()
    settings["albums_sort_reverse"] = False
    a = Album("dir1", settings, album["subdirs"], album["medias"], gal)
    a.sort_subdirs("title")
    assert [im.title for im in a.albums] == titles

    settings["albums_sort_reverse"] = True
    a = Album("dir1", settings, album["subdirs"], album["medias"], gal)
    a.sort_subdirs("title")
    assert [im.title for im in a.albums] == list(reversed(titles))

    orders = ["-10", "02", "03"]
    settings["albums_sort_reverse"] = False
    a = Album("dir1", settings, album["subdirs"], album["medias"], gal)
    a.sort_subdirs("meta.order")
    assert [d.meta["order"][0] for d in a.albums] == orders

    settings["albums_sort_reverse"] = True
    a = Album("dir1", settings, album["subdirs"], album["medias"], gal)
    a.sort_subdirs("meta.order")
    assert [d.meta["order"][0] for d in a.albums] == list(reversed(orders))

    settings["albums_sort_reverse"] = False
    a = Album("dir1", settings, album["subdirs"], album["medias"], gal)
    a.sort_subdirs(["meta.partialorder", "meta.order"])
    assert [d.name for d in a.albums] == list(["test1", "test2", "test3"])

    settings["albums_sort_reverse"] = False
    a = Album("dir1", settings, album["subdirs"], album["medias"], gal)
    a.sort_subdirs(["meta.partialorderb", "name"])
    assert [d.name for d in a.albums] == list(["test2", "test3", "test1"])

    settings["albums_sort_reverse"] = True
    a = Album("dir1", settings, album["subdirs"], album["medias"], gal)
    a.sort_subdirs(["meta.partialorderb", "name"])
    assert [d.name for d in a.albums] == list(["test1", "test3", "test2"])


def test_medias_sort(settings):
    gal = Gallery(settings, ncpu=1)
    album = REF["dir1/test2"]

    settings["medias_sort_reverse"] = True
    a = Album("dir1/test2", settings, album["subdirs"], album["medias"], gal)
    a.sort_medias(settings["medias_sort_attr"])
    assert [im.dst_filename for im in a.images] == list(reversed(album["medias"]))

    settings["medias_sort_attr"] = "date"
    settings["medias_sort_reverse"] = False
    a = Album("dir1/test2", settings, album["subdirs"], album["medias"], gal)
    a.sort_medias(settings["medias_sort_attr"])
    assert a.medias[0].src_filename == "22.jpg"

    settings["medias_sort_attr"] = "meta.order"
    settings["medias_sort_reverse"] = False
    a = Album("dir1/test2", settings, album["subdirs"], album["medias"], gal)
    a.sort_medias(settings["medias_sort_attr"])
    assert [im.dst_filename for im in a.images] == [
        "21.tiff",
        "22.jpg",
        "CMB_Timeline300_no_WMAP.jpg",
    ]


def test_gallery(settings, tmp_path, caplog):
    "Test the Gallery class."

    caplog.set_level("ERROR")
    settings["destination"] = str(tmp_path)
    settings["user_css"] = str(tmp_path / "my.css")
    settings["webm_options"] = ["-missing-option", "foobar"]
    gal = Gallery(settings, ncpu=1)

    gal.build()

    if HAS_HEIF:
        assert re.match(r"CSS file .* could not be found", caplog.records[3].message)
    else:
        assert re.match(r"CSS file .* could not be found", caplog.records[4].message)

    with open(tmp_path / "my.css", mode="w") as f:
        f.write("color: red")

    gal.build()

    mycss = os.path.join(settings["destination"], "static", "my.css")
    assert os.path.isfile(mycss)

    out_html = os.path.join(settings["destination"], "index.html")
    assert os.path.isfile(out_html)

    with open(out_html) as f:
        html = f.read()

    assert "<title>Sigal test gallery - Sigal test gallery ☺</title>" in html
    assert '<link rel="stylesheet" href="./static/my.css">' in html

    logger = logging.getLogger("sigal")
    logger.setLevel(logging.DEBUG)
    try:
        gal = Gallery(settings, ncpu=1)
        with pytest.raises(SubprocessException):
            gal.build()
    finally:
        logger.setLevel(logging.INFO)


def test_custom_theme(settings, tmp_path, caplog):
    theme_path = tmp_path / "mytheme"
    tpl_path = theme_path / "templates"

    settings["destination"] = str(tmp_path / "build")
    settings["source"] = os.path.join(settings["source"], "encryptTest")
    settings["theme"] = str(theme_path)
    settings["title"] = "My gallery"

    gal = Gallery(settings, ncpu=1)

    with pytest.raises(Exception, match="Impossible to find the theme"):
        gal.build()

    tpl_path.mkdir(parents=True)
    (theme_path / "static").mkdir(parents=True)

    with pytest.raises(SystemExit):
        gal.build()
        assert caplog.records[0].message.startswith(
            "The template album.html was not found in template folder"
        )

    with open(tpl_path / "album.html", mode="w") as f:
        f.write(""" {{ settings.title|myfilter }} """)
    with open(tpl_path / "album_list.html", mode="w") as f:
        f.write(""" {{ settings.title|myfilter }} """)
    with open(theme_path / "filters.py", mode="w") as f:
        f.write(
            """
def myfilter(value):
    return f'{value} is very nice'
"""
        )

    gal = Gallery(settings, ncpu=1)
    gal.build()

    out_html = os.path.join(settings["destination"], "index.html")
    assert os.path.isfile(out_html)

    with open(out_html) as f:
        html = f.read()

    assert "My gallery is very nice" in html


def test_gallery_max_img_pixels(settings, tmpdir, monkeypatch):
    "Test the Gallery class with the max_img_pixels setting."
    # monkeypatch is used here to reset the value to the PIL default.
    # This value does not matter, other than it is "large"
    # to show that settings['max_img_pixels'] works.
    monkeypatch.setattr("PIL.Image.MAX_IMAGE_PIXELS", 100_000_000)

    settings["source"] = os.path.join(settings["source"], "dir2")
    settings["destination"] = str(tmpdir)
    settings["max_img_pixels"] = 5000

    logger = logging.getLogger("sigal")
    logger.setLevel(logging.DEBUG)
    try:
        with pytest.raises(PILImage.DecompressionBombError):
            gal = Gallery(settings, ncpu=1)
            gal.build()

        settings["max_img_pixels"] = 100_000_000
        gal = Gallery(settings, ncpu=1)
        gal.build()
    finally:
        logger.setLevel(logging.INFO)


def test_empty_dirs(settings):
    gal = Gallery(settings, ncpu=1)
    assert "empty" not in gal.albums
    assert "dir1/empty" not in gal.albums


def test_ignores(settings, tmp_path):
    settings["source"] = os.path.join(settings["source"], "dir1")
    settings["destination"] = str(tmp_path)
    settings["ignore_directories"] = ["*test2"]
    settings["ignore_files"] = ["*.gif", "*CMB_*"]
    gal = Gallery(settings, ncpu=1)
    gal.build()

    assert not (tmp_path / "test2").exists()
    assert not (tmp_path / "test1" / "example.gif").exists()
    assert not (tmp_path / "test1" / "CMB_Timeline300_no_WMAP.jpg").exists()


@pytest.mark.parametrize("thumbnail", ["outdoor.heic", "outdoor.tn.jpg"])
def test_thumbnail_with_img_format(settings, tmp_path, thumbnail):
    """Test that outdoor.heic is correctly converted as jpg and used as thumbnail"""
    pytest.importorskip("pillow_heif")
    src_path = tmp_path / "pictures"
    src_path.mkdir()
    shutil.copytree(
        os.path.join(settings["source"], "dir1", "test1"), src_path / "test1"
    )
    desc = (src_path / "test1" / "index.md").read_text()
    desc = desc.replace("Thumbnail: 11.jpg", f"Thumbnail: {thumbnail}")
    (src_path / "test1" / "index.md").write_text(desc)

    settings["img_format"] = "JPEG"
    settings["thumb_dir"] = ""
    settings["source"] = str(src_path)
    settings["destination"] = str(tmp_path / "build")
    gal = Gallery(settings, ncpu=1)
    gal.build()

    assert (tmp_path / "build" / "test1" / "outdoor.tn.jpg").is_file()
    index = (tmp_path / "build" / "index.html").read_text()
    assert 'src="./test1/outdoor.tn.jpg" class="album_thumb"' in index


def test_polarsteps_map_route_and_creation_date_grouping(settings, tmp_path):
    class CustomFakeMedia:
        def __init__(self, path, filename, thumb_name, gps, date, title):
            self.path = path
            self.src_filename = filename
            self.dst_filename = filename
            self.thumb_name = thumb_name
            self.gps = gps
            self.date = date
            self.title = title
            self.type = "image"
            self.description = "Test description"
            self.big = None

    gal = SimpleNamespace(albums={})
    album = Album("trip", settings, [], [], gal)

    # Media 1 has GPS location; Media 2 has NO GPS, but has creation date on the same day
    m1 = CustomFakeMedia("trip", "img1.jpg", "thumb1.jpg", {"lat": 48.8566, "lon": 2.3522}, datetime.datetime(2026, 8, 1, 10, 0, 0), "Eiffel Tower")
    m2 = CustomFakeMedia("trip", "img2.jpg", "thumb2.jpg", None, datetime.datetime(2026, 8, 1, 14, 0, 0), "Louvre Museum")
    m3 = CustomFakeMedia("trip", "img3.jpg", "thumb3.jpg", {"lat": 45.7640, "lon": 4.8357}, datetime.datetime(2026, 8, 2, 11, 0, 0), "Lyon City")

    album.medias = [m1, m2, m3]

    markers = album.map_markers
    assert len(markers) == 2
    # Stop 1 (Paris) should group m1 and m2 together
    assert markers[0]["lat"] == 48.8566
    assert markers[0]["count"] == 2
    assert len(markers[0]["items"]) == 2
    assert markers[0]["items"][0]["caption"] == "Eiffel Tower"
    assert markers[0]["items"][1]["caption"] == "Louvre Museum"

    # Stop 2 (Lyon)
    assert markers[1]["lat"] == 45.7640
    assert markers[1]["count"] == 1

    # Check route
    assert len(album.route) == 2
    assert album.route[0] == {"lat": 48.8566, "lon": 2.3522}
    assert album.route[1] == {"lat": 45.7640, "lon": 4.8357}

    # Render map template
    settings["destination"] = str(tmp_path)
    settings["show_map"] = True
    settings["theme"] = "photobook"
    writer = AlbumPageWriter(settings, index_title="Test Gallery")
    template = writer.template.environment.get_template("map.html")
    html = template.render(album=album, settings=settings)

    assert "sigal-map-container" in html
    assert "itinerary-bar" in html
    assert "exportRouteGPX" in html
    assert "exportRouteKML" in html
    assert "loc-album-modal" in html
    assert "loc-lightbox" in html
    assert "Eiffel Tower" in html
    assert "Louvre Museum" in html

    # Check GPX and KML generation
    assert "<gpx" in album.gpx
    assert '<wpt lat="48.8566" lon="2.3522">' in album.gpx
    assert "<kml" in album.kml
    assert "<coordinates>2.3522,48.8566,0</coordinates>" in album.kml

    # Test file writing
    album.dst_path = str(tmp_path)
    album.output_file = "index.html"
    writer.write(album)
    assert (tmp_path / "route.gpx").is_file()
    assert (tmp_path / "route.kml").is_file()
    assert "<gpx" in (tmp_path / "route.gpx").read_text()
    assert "<kml" in (tmp_path / "route.kml").read_text()


