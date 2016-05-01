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


def test_url_from_windows_path(monkeypatch):
    monkeypatch.setattr('os.sep', "\\")
    path = os.sep.join(['foo', 'bar'])
    assert path == r'foo\bar'
    assert utils.url_from_path(path) == 'foo/bar'


def test_read_markdown():
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir1', 'test1', '11.md')
    m = utils.read_markdown(src)
    assert m['title'] == "Foo Bar"
    assert m['meta']['location'][0] == "Bavaria"
    assert m['description'] == \
        "<p>This is a funny description of this image</p>"


def test_read_markdown_empty_file(tmpdir):
    src = tmpdir.join("file.txt")
    src.write("content")
    m = utils.read_markdown(str(src))
    assert 'title' not in m
    assert m['meta'] == {}
    assert m['description'] == '<p>content</p>'

    src = tmpdir.join("empty.txt")
    src.write("")
    m = utils.read_markdown(str(src))
    assert 'title' not in m
    assert 'meta' not in m
    assert m['description'] == ''


def test_call_subprocess():
    returncode, stdout, stderr = utils.call_subprocess(['echo', 'ok'])
    assert returncode == 0
    assert stdout == 'ok\n'
    assert stderr == ''

    # returncode, stdout, stderr = utils.call_subprocess(['/usr/bin/false'])
    # assert returncode == 1


def test_is_valid_html5_video():
    assert utils.is_valid_html5_video('.webm') is True
    assert utils.is_valid_html5_video('.mpeg') is False
