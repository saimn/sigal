# -*- coding:utf-8 -*-

import os
import pytest

from sigal.gallery import Gallery, PathsDb, get_metadata, copy
from sigal.settings import read_settings

CURRENT_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(CURRENT_DIR, 'sample')

REF = {
    'dir1': {
        'title': 'An example gallery',
        'thumbnail': 'test1/11.jpg',
        'medias': [],
    },
    'dir1/test1': {
        'title': 'An example sub-category',
        'thumbnail': '11.jpg',
        'medias': ['11.jpg', 'archlinux-kiss-1024x640.png',
                   'flickr_jerquiaga_2394751088_cc-by-nc.jpg'],
    },
    'dir1/test2': {
        'title': 'Test2',
        'thumbnail': '21.jpg',
        'medias': ['21.jpg', '22.jpg'],
    },
    'dir2': {
        'title': 'Another example gallery with a very long name',
        'thumbnail': 'm57_the_ring_nebula-587px.jpg',
        'medias': ['exo20101028-b-full.jpg',
                   'm57_the_ring_nebula-587px.jpg',
                   'Hubble ultra deep field.jpg',
                   'Hubble Interacting Galaxy NGC 5257.jpg'],
    },
    u'accentué': {
        'title': u'Accentué',
        'thumbnail': u'hélicoïde.jpg',
        'medias': [u'hélicoïde.jpg', 'superdupont_source_wikipedia_en.jpg'],
    },
    'video': {
        'title': 'Video',
        'thumbnail': 'stallman-software-freedom-day-low.ogv',
        'medias': ['stallman-software-freedom-day-low.ogv']
    }
}


@pytest.fixture(scope='module')
def paths():
    """Read the sample config file and build the PathsDb object."""

    default_conf = os.path.join(SAMPLE_DIR, 'sigal.conf.py')
    settings = read_settings(default_conf)
    return PathsDb(os.path.join(SAMPLE_DIR, 'pictures'),
                   settings['img_ext_list'], settings['vid_ext_list'])


@pytest.fixture(scope='module')
def db(paths):
    paths.build()
    return paths.db


def test_filelist(db):
    assert set(db.keys()) == set([
        'paths_list', 'skipped_dir', '.', 'dir1', 'dir2', 'dir1/test1',
        'dir1/test2', u'accentué', 'video'])

    assert set(db['paths_list']) == set([
        '.', 'dir1', 'dir1/test1', 'dir1/test2', 'dir2', u'accentué', 'video'])

    assert set(db['skipped_dir']) == set(['empty', 'dir1/empty'])
    assert db['.']['medias'] == []
    assert set(db['.']['subdir']) == set([u'accentué', 'dir1', 'dir2',
                                          'video'])


def test_title(db):
    for p in REF.keys():
        assert db[p]['title'] == REF[p]['title']


def test_thumbnail(db):
    for p in REF.keys():
        assert db[p]['thumbnail'] == REF[p]['thumbnail']


def test_medialist(db):
    for p in REF.keys():
        assert set(db[p]['medias']) == set(REF[p]['medias'])


def test_get_subdir(paths):
    assert set(paths.get_subdirs('dir1/test1')) == set()
    assert set(paths.get_subdirs('dir1')) == set(['dir1/test1', 'dir1/test2'])
    assert set(paths.get_subdirs('.')) == set([
        'dir1', 'dir2', 'dir1/test1', 'dir1/test2', u'accentué', 'video'])


def test_get_metadata():
    "Test the get_metadata function."

    m = get_metadata(os.path.join(SAMPLE_DIR, 'pictures', 'dir1'))
    assert m['title'] == REF['dir1']['title']
    assert m['thumbnail'] == ''

    m = get_metadata(os.path.join(SAMPLE_DIR, 'pictures', 'dir2'))
    assert m['title'] == REF['dir2']['title']
    assert m['thumbnail'] == REF['dir2']['thumbnail']


def test_gallery(tmpdir):
    "Test the Gallery class."

    default_conf = os.path.join(SAMPLE_DIR, 'sigal.conf.py')
    settings = read_settings(default_conf)
    settings['destination'] = str(tmpdir)
    gal = Gallery(settings)
    gal.build()

    out_html = os.path.join(settings['destination'], 'index.html')
    assert os.path.isfile(out_html)

    with open(out_html, 'r') as f:
        html = f.read()

    assert '<title>Sigal test gallery</title>' in html


def test_copy(tmpdir):
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2',
                       REF['dir2']['medias'][0])
    dst = str(tmpdir.join(REF['dir2']['medias'][0]))
    copy(src, dst)
    assert os.path.isfile(dst)

    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2',
                       REF['dir2']['medias'][1])
    dst = str(tmpdir.join(REF['dir2']['medias'][1]))
    copy(src, dst, symlink=True)
    assert os.path.islink(dst)
