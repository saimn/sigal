import os
from pathlib import Path
from sigal import utils

CURRENT_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(CURRENT_DIR, 'sample')


def test_copy(tmpdir):
    filename = 'KeckObservatory20071020.jpg'
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

    filename = 'KeckObservatory20071020.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    utils.copy(src, dst, symlink=True)
    assert os.path.islink(dst)
    assert os.readlink(dst) == src

    filename = 'KeckObservatory20071020.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    dst = str(tmpdir.join(filename))
    utils.copy(src, dst, symlink=True, rellink=True)
    assert os.path.islink(dst)
    assert os.path.join(os.path.dirname(CURRENT_DIR)), os.readlink(dst) == src
    # get absolute path of the current dir plus the relative dir

    src = str(tmpdir.join('foo.txt'))
    dst = str(tmpdir.join('bar.txt'))
    p = Path(src)
    p.touch()
    p.chmod(0o444)
    utils.copy(src, dst)
    utils.copy(src, dst)


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
    # See https://github.com/Python-Markdown/markdown/pull/672
    # Meta attributes should always be there
    assert m['meta'] == {}
    assert m['description'] == ''


def test_is_valid_html5_video():
    assert utils.is_valid_html5_video('.webm') is True
    assert utils.is_valid_html5_video('.mpeg') is False
