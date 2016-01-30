# -*- coding:utf-8 -*-

import locale
import logging
import os
import pytest
import datetime

from os.path import join
from sigal.gallery import Album, Media, Image, Video, Gallery
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
        'medias': ['11.jpg', 'archlinux-kiss-1024x640.png',
                   'flickr_jerquiaga_2394751088_cc-by-nc.jpg',
                   '50a1d0bc-763d-457e-b634-c87f16a64270.gif'],
    },
    'dir1/test2': {
        'title': 'test2',
        'name': 'test2',
        'thumbnail': 'test2/thumbnails/21.tn.jpg',
        'subdirs': [],
        'medias': ['21.jpg', '22.jpg', 'archlinux-kiss-1024x640.png'],
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
        'medias': ['exo20101028-b-full.jpg',
                   'Hubble Interacting Galaxy NGC 5257.jpg',
                   'Hubble ultra deep field.jpg',
                   'm57_the_ring_nebula-587px.jpg'],
    },
    u'accentué': {
        'title': u'accentué',
        'name': u'accentué',
        'thumbnail': u'accentué/thumbnails/hélicoïde.tn.jpg',
        'subdirs': [],
        'medias': [u'hélicoïde.jpg', 'superdupont_source_wikipedia_en.jpg'],
    },
    'video': {
        'title': 'video',
        'name': 'video',
        'thumbnail': ('video/thumbnails/'
                      'stallman software-freedom-day-low.tn.jpg'),
        'subdirs': [],
        'medias': ['stallman software-freedom-day-low.webm']
    }
}


def test_media(settings):
    m = Media('11.jpg', 'dir1/test1', settings)
    path = join('dir1', 'test1')
    file_path = join(path, '11.jpg')
    thumb = join('thumbnails', '11.tn.jpg')

    assert m.filename == '11.jpg'
    assert m.src_path == join(settings['source'], file_path)
    assert m.dst_path == join(settings['destination'], file_path)
    assert m.thumb_name == thumb
    assert m.thumb_path == join(settings['destination'], path, thumb)
    assert m.title == "Foo Bar"
    assert m.description == "<p>This is a funny description of this image</p>"

    assert repr(m) == "<Media>('{}')".format(file_path)
    assert str(m) == file_path


def test_media_orig(settings, tmpdir):
    settings['keep_orig'] = False
    m = Media('11.jpg', 'dir1/test1', settings)
    assert m.big is None

    settings['keep_orig'] = True
    settings['destination'] = str(tmpdir)

    m = Image('11.jpg', 'dir1/test1', settings)
    assert m.big == 'original/11.jpg'

    m = Video('stallman software-freedom-day-low.ogv', 'video', settings)
    assert m.filename == 'stallman software-freedom-day-low.webm'
    assert m.big == 'original/stallman software-freedom-day-low.ogv'
    assert os.path.isfile(join(settings['destination'], m.path, m.big))

    settings['use_orig'] = True

    m = Image('21.jpg', 'dir1/test2', settings)
    assert m.big == '21.jpg'


def test_image(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    m = Image('11.jpg', 'dir1/test1', settings)
    assert m.date == datetime.datetime(2006, 1, 22, 10, 32, 42)
    assert m.exif['datetime'] == u'Sunday, 22. January 2006'

    os.makedirs(join(settings['destination'], 'dir1', 'test1', 'thumbnails'))
    assert m.thumbnail == join('thumbnails', '11.tn.jpg')
    assert os.path.isfile(m.thumb_path)


def test_video(settings, tmpdir):
    settings['destination'] = str(tmpdir)
    m = Video('stallman software-freedom-day-low.ogv', 'video', settings)
    file_path = join('video', 'stallman software-freedom-day-low.webm')
    assert str(m) == file_path
    assert m.dst_path == join(settings['destination'], file_path)

    os.makedirs(join(settings['destination'], 'video', 'thumbnails'))
    assert m.thumbnail == join('thumbnails',
                               'stallman software-freedom-day-low.tn.jpg')
    assert os.path.isfile(m.thumb_path)


@pytest.mark.parametrize("path,album", REF.items())
def test_album(path, album, settings, tmpdir):
    # store current locale
    old_locale = locale.setlocale(locale.LC_ALL)

    # locale.setlocale(locale.LC_ALL, 'fr_FR')
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

    gal = Gallery(settings, ncpu=1)
    a = Album(path, settings, album['subdirs'], album['medias'], gal)

    assert a.title == album['title']
    assert a.name == album['name']
    assert a.subdirs == album['subdirs']
    assert a.thumbnail == album['thumbnail']
    assert [m.filename for m in a.medias] == album['medias']
    assert len(a) == len(album['medias'])

    # restore locale back
    locale.setlocale(locale.LC_ALL, old_locale)


def test_album_medias(settings):
    gal = Gallery(settings, ncpu=1)

    album = REF['dir1/test1']
    a = Album('dir1/test1', settings, album['subdirs'], album['medias'], gal)
    assert list(im.filename for im in a.images) == album['medias']
    assert list(a.videos) == []

    album = REF['video']
    a = Album('video', settings, album['subdirs'], album['medias'], gal)
    assert list(im.filename for im in a.videos) == album['medias']
    assert list(a.images) == []


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


def test_medias_sort(settings):
    gal = Gallery(settings, ncpu=1)
    album = REF['dir1/test2']

    settings['medias_sort_reverse'] = True
    a = Album('dir1/test2', settings, album['subdirs'], album['medias'], gal)
    a.sort_medias(settings['medias_sort_attr'])
    assert [im.filename for im in a.images] == list(reversed(album['medias']))

    settings['medias_sort_attr'] = 'date'
    settings['medias_sort_reverse'] = False
    a = Album('dir1/test2', settings, album['subdirs'], album['medias'], gal)
    a.sort_medias(settings['medias_sort_attr'])
    assert [im.filename for im in a.images] == ['22.jpg', '21.jpg',
                                                'archlinux-kiss-1024x640.png']


def test_gallery(settings, tmpdir):
    "Test the Gallery class."

    settings['destination'] = str(tmpdir)
    settings['webm_options'] = ['-missing-option', 'foobar']

    gal = Gallery(settings, ncpu=1)
    gal.build()

    out_html = os.path.join(settings['destination'], 'index.html')
    assert os.path.isfile(out_html)

    with open(out_html, 'r') as f:
        html = f.read()

    assert '<title>Sigal test gallery</title>' in html

    logger = logging.getLogger('sigal')
    logger.setLevel(logging.DEBUG)
    try:
        gal = Gallery(settings, ncpu=1)
        with pytest.raises(SubprocessException):
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
    settings['ignore_directories'] = ['*test2']
    settings['ignore_files'] = ['dir2/Hubble*', '*.png']
    gal = Gallery(settings, ncpu=1)
    gal.build()

    assert 'test2' not in os.listdir(join(tmp, 'dir1'))
    assert 'archlinux-kiss-1024x640.png' not in os.listdir(
        join(tmp, 'dir1', 'test1'))
    assert 'Hubble Interacting Galaxy NGC 5257.jpg' not in os.listdir(
        join(tmp, 'dir2'))
