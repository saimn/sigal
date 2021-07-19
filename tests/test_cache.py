import os

from sigal.utils import read_markdown
from sigal.cache import Cache


CURRENT_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(CURRENT_DIR, 'sample')
TEST_META = os.path.join(SAMPLE_DIR, 'pictures/dir1/test1/11.md')


def test_no_cache(tmpdir):
    data = 'testing'
    with Cache({}) as c:
        assert c.read(TEST_META) is None
        c.write(TEST_META, data)
        assert c.read(TEST_META) is None

    data = {'test': True}
    with Cache({}) as c:
        assert c.read_dict(TEST_META) is None
        c.write_dict(TEST_META, data)
        assert c.read_dict(TEST_META) is None


def test_cache(tmpdir):
    settings = {'cache': os.path.join(tmpdir, 'cache.sqlite')}
    data = 'testing'
    with Cache(settings) as c:
        assert c.read(TEST_META) is None
        c.write(TEST_META, data)
        assert c.read(TEST_META) == data

    assert os.path.isfile(settings['cache'])

    with Cache(settings) as c:
        assert c.read(TEST_META) == data


def test_cache_dict(tmpdir):
    settings = {'cache': os.path.join(tmpdir, 'cache.sqlite')}
    data = read_markdown(TEST_META)
    with Cache(settings) as c:
        assert c.read_dict(TEST_META) is None
        c.write_dict(TEST_META, data)
        assert c.read_dict(TEST_META) == data

    assert os.path.isfile(settings['cache'])

    with Cache(settings) as c:
        assert c.read_dict(TEST_META) == data


def test_invalid_cache(tmpdir):
    """
    Test an invalid cache file.
    Should delete bad file and continue.
    """
    settings = {'cache': os.path.join(tmpdir, 'cache.sqlite')}
    with open(settings['cache'], 'w') as f:
        f.write('invalid')

    data = 'testing'
    with Cache(settings) as c:
        assert c.read(TEST_META) is None
        c.write(TEST_META, data)
        assert c.read(TEST_META) == data

    assert os.path.isfile(settings['cache'])

    with Cache(settings) as c:
        assert c.read(TEST_META) == data


def test_cache_exception(tmpdir):
    """
    Test what happens when an exception occurs.
    Cache should not be saved.
    """
    settings = {'cache': os.path.join(tmpdir, 'cache.sqlite')}
    data = 'testing'
    try:
        with Cache(settings) as c:
            assert c.read(TEST_META) is None
            c.write(TEST_META, data)
            assert c.read(TEST_META) == data
            raise RuntimeError()
    except RuntimeError:
        pass

    assert not os.path.isfile(settings['cache'])

    with Cache(settings) as c:
        assert c.read(TEST_META) is None
