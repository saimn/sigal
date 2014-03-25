# -*- coding: utf-8 -*-

import os
from sigal.utils import copy, check_or_create_dir, url_from_path

CURRENT_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(CURRENT_DIR, 'sample')


def test_copy(tmpdir):
    filename = 'exo20101028-b-full.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    dst = str(tmpdir.join(filename))
    copy(src, dst)
    assert os.path.isfile(dst)

    filename = 'm57_the_ring_nebula-587px.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    dst = str(tmpdir.join(filename))
    copy(src, dst, symlink=True)
    assert os.path.islink(dst)
    assert os.readlink(dst) == src

    filename = 'exo20101028-b-full.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    copy(src, dst, symlink=True)
    assert os.path.islink(dst)
    assert os.readlink(dst) == src


def test_check_or_create_dir(tmpdir):
    path = str(tmpdir.join('new_directory'))
    check_or_create_dir(path)
    assert os.path.isdir(path)


def test_url_from_path():
    assert url_from_path(os.sep.join(['foo', 'bar'])) == 'foo/bar'
