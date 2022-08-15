import datetime
import logging
import os
import re
from os.path import join

import pytest
from PIL import Image as PILImage

from sigal.gallery import Album, Gallery, Image, Media, Video
from sigal.video import SubprocessException

CURRENT_DIR = os.path.dirname(__file__)

REF = {
    'dir1': {
        'title': 'An example gallery',
        'name': 'dir1',
        'thumbnail': 'dir1/test1/thumbnails/11.tn.jpg',
        'subdirs': ['test1', 'test2', 'test3'],
        'medias': [],
    },
    'dir1/test1': {
        'title': 'An example sub-category',
        'name': 'test1',
        'thumbnail': 'test1/thumbnails/11.tn.jpg',
        'subdirs': [],
        'medias': [
            '11.jpg',
            'CMB_Timeline300_no_WMAP.jpg',
            'flickr_jerquiaga_2394751088_cc-by-nc.jpg',
            'example.gif',
        ],
    },
    'dir1/test2': {
        'title': 'test2',
        'name': 'test2',
        'thumbnail': 'test2/thumbnails/21.tn.tiff',
        'subdirs': [],
        'medias': ['21.tiff', '22.jpg', 'CMB_Timeline300_no_WMAP.jpg'],
    },
    'dir1/test3': {
        'title': '01 First title alphabetically',
        'name': 'test3',
        'thumbnail': 'test3/thumbnails/3.tn.jpg',
        'subdirs': [],
        'medias': ['3.jpg'],
    },
    'dir2': {
        'title': 'Another example gallery with a very long name',
        'name': 'dir2',
        'thumbnail': 'dir2/thumbnails/m57_the_ring_nebula-587px.tn.jpg',
        'subdirs': [],
        'medias': [
            'KeckObservatory20071020.jpg',
            'Hubble Interacting Galaxy NGC 5257.jpg',
            'Hubble ultra deep field.jpg',
            'm57_the_ring_nebula-587px.jpg',
        ],
    },
    'accentué': {
        'title': 'accentué',
        'name': 'accentué',
        'thumbnail': 'accentu%C3%A9/thumbnails/h%C3%A9lico%C3%AFde.tn.jpg',
        'subdirs': [],
        'medias': ['hélicoïde.jpg', '11.jpg'],
    },
    'video': {
        'title': 'video',
        'name': 'video',
        'thumbnail': 'video/thumbnails/example%20video.tn.jpg',
        'subdirs': [],
        'medias': ['example video.ogv'],
    },
    'webp': {
        'title': 'webp',
        'name': 'webp',
        'thumbnail': 'webp/thumbnails/_MG_7805_lossy80.tn.webp',
        'subdirs': [],
        'medias': ['_MG_7805_lossy80.webp', '_MG_7808_lossy80.webp'],
    },
}


def test_media(settings):
    m = Media('11.jpg', 'dir1/test1', settings)
    path = join('dir1', 'test1')
    file_path = join(path, '11.jpg')
    thumb = join('thumbnails', '11.tn.jpg')

    assert m.dst_filename == '11.jpg'
    assert m.src_path == join(settings['source'], file_path)
    assert m.dst_path == join(settings['destination'], file_path)
    assert m.thumb_name == thumb
    assert m.thumb_path == join(settings['destination'], path, thumb)
    assert m.title == "Foo Bar"
    assert m.description == "<p>This is a funny description of this image</p>"

    assert repr(m) == f"<Media>('{file_path}')"
    assert str(m) == file_path


def test_media_orig(settings, tmpdir):
    settings['keep_orig'] = False
    m = Media('11.jpg', 'dir1/test1', settings)
    assert m.big is None

    settings['keep_orig'] = True
    settings['destination'] = str(tmpdir)

    m = Image('11.jpg', 'dir1/test1', settings)
    assert m.big == 'original/11.jpg'

    m = Video('example video.ogv', 'video', settings)
    assert m.dst_filename == 'example video.webm'
    assert m.big_url == 'original/example%20video.ogv'
    assert os.path.isfile(join(settings['destination'], m.path, m.big))

    settings['use_orig'] = True

    m = Image('21.jpg', 'dir1/test2', settings)
    assert m.big == '21.jpg'


def test_media_iptc_override(settings):
    img_with_md = Image('2.jpg', 'iptcTest', settings)
    assert img_with_md.title == "Markdown title beats iptc"
    # Markdown parsing adds formatting. Let's just focus on content
    assert "Markdown description beats iptc" in img_with_md.description
    img_no_md = Image('1.jpg', 'iptcTest', settings)
    assert (
        img_no_md.title
        == 'Haemostratulus clouds over Canberra - 2005-12-28 at 03-25-07'
    )
    assert (
        img_no_md.description
        == '"Haemo" because they look like haemoglobin '
        'cells and "stratulus" because I can\'t work out whether '
        'they\'re Stratus or Cumulus clouds.\nWe\'re driving down '
        'the main drag in Canberra so it\'s Parliament House that '
        'you can see at the end of the road.'
    )


def test_media_img_format(settings):
    settings['img_format'] = 'jpeg'
    m = Image('11.tiff', 'dir1/test1', settings)
    path = join('dir1', 'test1')
    thumb = join('thumbnails', '11.tn.jpeg')

    assert m.dst_filename == '11.jpeg'
    assert m.src_path == join(settings['source'], path, '11.tiff')
    assert m.dst_path == join(settings['destination'], path, '11.jpeg')
    assert m.thumb_name == thumb
    assert m.thumb_path == join(settings['destination'], path, thumb)
    assert m.title == "Foo Bar"
    assert m.description == "<p>This is a funny description of this image</p>"

    file_path = join(path, '11.tiff')
    assert repr(m) == f"<Image>('{file_path}')"
    assert str(m) == file_path


def test_image(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    settings['datetime_format'] = '%d/%m/%Y'
    m = Image('11.jpg', 'dir1/test1', settings)
    assert m.date == datetime.datetime(2006, 1, 22, 10, 32, 42)
    assert m.exif['datetime'] == '22/01/2006'

    os.makedirs(join(settings['destination'], 'dir1', 'test1', 'thumbnails'))
    assert m.thumbnail == join('thumbnails', '11.tn.jpg')
    assert os.path.isfile(m.thumb_path)


def test_video(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    m = Video('example video.ogv', 'video', settings)

    src_path = join('video', 'example video.ogv')
    assert str(m) == src_path

    file_path = join('video', 'example video.webm')
    assert m.dst_path == join(settings['destination'], file_path)

    os.makedirs(join(settings['destination'], 'video', 'thumbnails'))
    assert m.thumbnail == join('thumbnails', 'example%20video.tn.jpg')
    assert os.path.isfile(m.thumb_path)


@pytest.mark.parametrize("path,album", REF.items())
def test_album(path, album, settings, tmpdir):
    gal = Gallery(settings, ncpu=1)
    a = Album(path, settings, album['subdirs'], album['medias'], gal)

    assert a.title == album['title']
    assert a.name == album['name']
    assert a.subdirs == album['subdirs']
    assert a.thumbnail == album['thumbnail']
    if path == 'video':
        assert list(a.images) == []
        assert [m.dst_filename for m in a.medias] == [
            album['medias'][0].replace('.ogv', '.webm')
        ]
    else:
        assert list(a.videos) == []
        assert [m.dst_filename for m in a.medias] == album['medias']
    assert len(a) == len(album['medias'])


def test_albums_sort(settings):
    gal = Gallery(settings, ncpu=1)
    album = REF['dir1']
    subdirs = list(album['subdirs'])

    settings['albums_sort_reverse'] = False
    a = Album('dir1', settings, album['subdirs'], album['medias'], gal)
    a.sort_subdirs('')
    assert [alb.name for alb in a.albums] == subdirs

    settings['albums_sort_reverse'] = True
    a = Album('dir1', settings, album['subdirs'], album['medias'], gal)
    a.sort_subdirs('')
    assert [alb.name for alb in a.albums] == list(reversed(subdirs))

    titles = [im.title for im in a.albums]
    titles.sort()
    settings['albums_sort_reverse'] = False
    a = Album('dir1', settings, album['subdirs'], album['medias'], gal)
    a.sort_subdirs('title')
    assert [im.title for im in a.albums] == titles

    settings['albums_sort_reverse'] = True
    a = Album('dir1', settings, album['subdirs'], album['medias'], gal)
    a.sort_subdirs('title')
    assert [im.title for im in a.albums] == list(reversed(titles))

    orders = ['01', '02', '03']
    orders.sort()
    settings['albums_sort_reverse'] = False
    a = Album('dir1', settings, album['subdirs'], album['medias'], gal)
    a.sort_subdirs('meta.order')
    assert [d.meta['order'][0] for d in a.albums] == orders

    settings['albums_sort_reverse'] = True
    a = Album('dir1', settings, album['subdirs'], album['medias'], gal)
    a.sort_subdirs('meta.order')
    assert [d.meta['order'][0] for d in a.albums] == list(reversed(orders))

    settings['albums_sort_reverse'] = False
    a = Album('dir1', settings, album['subdirs'], album['medias'], gal)
    a.sort_subdirs(['meta.partialorder', 'meta.order'])
    assert [d.name for d in a.albums] == list(['test1', 'test2', 'test3'])

    settings['albums_sort_reverse'] = False
    a = Album('dir1', settings, album['subdirs'], album['medias'], gal)
    a.sort_subdirs(['meta.partialorderb', 'name'])
    assert [d.name for d in a.albums] == list(['test2', 'test3', 'test1'])

    settings['albums_sort_reverse'] = True
    a = Album('dir1', settings, album['subdirs'], album['medias'], gal)
    a.sort_subdirs(['meta.partialorderb', 'name'])
    assert [d.name for d in a.albums] == list(['test1', 'test3', 'test2'])


def test_medias_sort(settings):
    gal = Gallery(settings, ncpu=1)
    album = REF['dir1/test2']

    settings['medias_sort_reverse'] = True
    a = Album('dir1/test2', settings, album['subdirs'], album['medias'], gal)
    a.sort_medias(settings['medias_sort_attr'])
    assert [im.dst_filename for im in a.images] == list(reversed(album['medias']))

    settings['medias_sort_attr'] = 'date'
    settings['medias_sort_reverse'] = False
    a = Album('dir1/test2', settings, album['subdirs'], album['medias'], gal)
    a.sort_medias(settings['medias_sort_attr'])
    assert a.medias[0].src_filename == '22.jpg'

    settings['medias_sort_attr'] = 'meta.order'
    settings['medias_sort_reverse'] = False
    a = Album('dir1/test2', settings, album['subdirs'], album['medias'], gal)
    a.sort_medias(settings['medias_sort_attr'])
    assert [im.dst_filename for im in a.images] == [
        '21.tiff',
        '22.jpg',
        'CMB_Timeline300_no_WMAP.jpg',
    ]


def test_gallery(settings, tmp_path, caplog):
    "Test the Gallery class."

    caplog.set_level('ERROR')
    settings['destination'] = str(tmp_path)
    settings['user_css'] = str(tmp_path / 'my.css')
    settings['webm_options'] = ['-missing-option', 'foobar']
    gal = Gallery(settings, ncpu=1)

    gal.build()
    assert re.match(r'CSS file .* could not be found', caplog.records[3].message)

    with open(tmp_path / 'my.css', mode='w') as f:
        f.write('color: red')

    gal.build()

    mycss = os.path.join(settings['destination'], 'static', 'my.css')
    assert os.path.isfile(mycss)

    out_html = os.path.join(settings['destination'], 'index.html')
    assert os.path.isfile(out_html)

    with open(out_html) as f:
        html = f.read()

    assert '<title>Sigal test gallery - Sigal test gallery ☺</title>' in html
    assert '<link rel="stylesheet" href="static/my.css">' in html

    logger = logging.getLogger('sigal')
    logger.setLevel(logging.DEBUG)
    try:
        gal = Gallery(settings, ncpu=1)
        with pytest.raises(SubprocessException):
            gal.build()
    finally:
        logger.setLevel(logging.INFO)


def test_custom_theme(settings, tmp_path, caplog):
    theme_path = tmp_path / 'mytheme'
    tpl_path = theme_path / 'templates'

    settings['destination'] = str(tmp_path / 'build')
    settings['source'] = os.path.join(settings['source'], 'encryptTest')
    settings['theme'] = str(theme_path)
    settings['title'] = 'My gallery'

    gal = Gallery(settings, ncpu=1)

    with pytest.raises(Exception, match='Impossible to find the theme'):
        gal.build()

    tpl_path.mkdir(parents=True)
    (theme_path / 'static').mkdir(parents=True)

    with pytest.raises(SystemExit):
        gal.build()
        assert caplog.records[0].message.startswith(
            'The template album.html was not found in template folder'
        )

    with open(tpl_path / 'album.html', mode='w') as f:
        f.write(""" {{ settings.title|myfilter }} """)
    with open(tpl_path / 'album_list.html', mode='w') as f:
        f.write(""" {{ settings.title|myfilter }} """)
    with open(theme_path / 'filters.py', mode='w') as f:
        f.write(
            """
def myfilter(value):
    return f'{value} is very nice'
"""
        )

    gal = Gallery(settings, ncpu=1)
    gal.build()

    out_html = os.path.join(settings['destination'], 'index.html')
    assert os.path.isfile(out_html)

    with open(out_html) as f:
        html = f.read()

    assert 'My gallery is very nice' in html


def test_gallery_max_img_pixels(settings, tmpdir, monkeypatch):
    "Test the Gallery class with the max_img_pixels setting."
    # monkeypatch is used here to reset the value to the PIL default.
    # This value does not matter, other than it is "large"
    # to show that settings['max_img_pixels'] works.
    monkeypatch.setattr('PIL.Image.MAX_IMAGE_PIXELS', 100_000_000)

    with open(str(tmpdir.join('my.css')), mode='w') as f:
        f.write('color: red')

    settings['destination'] = str(tmpdir)
    settings['user_css'] = str(tmpdir.join('my.css'))
    settings['max_img_pixels'] = 5000

    logger = logging.getLogger('sigal')
    logger.setLevel(logging.DEBUG)
    try:
        with pytest.raises(PILImage.DecompressionBombError):
            gal = Gallery(settings, ncpu=1)
            gal.build()

        settings['max_img_pixels'] = 100_000_000
        gal = Gallery(settings, ncpu=1)
        gal.build()
    finally:
        logger.setLevel(logging.INFO)


def test_empty_dirs(settings):
    gal = Gallery(settings, ncpu=1)
    assert 'empty' not in gal.albums
    assert 'dir1/empty' not in gal.albums


def test_ignores(settings, tmpdir):
    tmp = str(tmpdir)
    settings['destination'] = tmp
    settings['ignore_directories'] = ['*test2', 'accentué']
    settings['ignore_files'] = ['dir2/Hubble*', '*.png', '*CMB_*']
    gal = Gallery(settings, ncpu=1)
    gal.build()

    assert 'test2' not in os.listdir(join(tmp, 'dir1'))
    assert 'accentué' not in os.listdir(tmp)
    assert 'CMB_Timeline300_no_WMAP.jpg' not in os.listdir(join(tmp, 'dir1', 'test1'))
    assert 'Hubble Interacting Galaxy NGC 5257.jpg' not in os.listdir(join(tmp, 'dir2'))
