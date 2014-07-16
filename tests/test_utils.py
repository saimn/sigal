# -*- coding: utf-8 -*-

import os
from sigal import utils

CURRENT_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(CURRENT_DIR, 'sample')


def test_copy(tmpdir):
    filename = 'exo20101028-b-full.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    dst = str(tmpdir.join(filename))
    utils.copy(src, dst)
    assert os.path.isfile(dst)

    filename = 'm57_the_ring_nebula-587px.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    dst = str(tmpdir.join(filename))
    utils.copy(src, dst, symlink=True)
    assert os.path.islink(dst)
    assert os.readlink(dst) == src

    filename = 'exo20101028-b-full.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    utils.copy(src, dst, symlink=True)
    assert os.path.islink(dst)
    assert os.readlink(dst) == src


def test_check_or_create_dir(tmpdir):
    path = str(tmpdir.join('new_directory'))
    utils.check_or_create_dir(path)
    assert os.path.isdir(path)


def test_url_from_path():
    assert utils.url_from_path(os.sep.join(['foo', 'bar'])) == 'foo/bar'


def test_read_markdown():
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir1', 'test1', '11.md')
    m = utils.read_markdown(src)
    assert m['title'] == "Foo Bar"
    assert m['meta']['location'][0] == "Bavaria"
    assert m['description'] == \
        "<p>This is a funny description of this image</p>"
