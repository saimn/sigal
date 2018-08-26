import os

from sigal.settings import read_settings, get_thumb

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


def test_read_settings(settings):
    """Test that the settings are correctly read."""
    assert settings['img_size'] == (640, 480)
    assert settings['thumb_size'] == (200, 150)
    assert settings['thumb_suffix'] == '.tn'
    assert settings['source'] == os.path.join(CURRENT_DIR, 'sample',
                                              'pictures')


def test_get_thumb(settings):
    """Test the get_thumb function."""
    tests = [('example.jpg', 'thumbnails/example.tn.jpg'),
             ('test/example.jpg', 'test/thumbnails/example.tn.jpg'),
             ('test/t/example.jpg', 'test/t/thumbnails/example.tn.jpg')]
    for src, ref in tests:
        assert get_thumb(settings, src) == ref

    tests = [('example.webm', 'thumbnails/example.tn.jpg'),
             ('test/example.mp4', 'test/thumbnails/example.tn.jpg'),
             ('test/t/example.avi', 'test/t/thumbnails/example.tn.jpg')]
    for src, ref in tests:
        assert get_thumb(settings, src) == ref


def test_img_sizes(tmpdir):
    """Test that image size is swaped if needed."""

    conf = tmpdir.join('sigal.conf.py')
    conf.write("thumb_size = (150, 200)")

    settings = read_settings(str(conf))
    assert settings['thumb_size'] == (200, 150)


def test_theme_path(tmpdir):
    """Test that image size is swaped if needed."""

    tmpdir.join('theme').mkdir()
    tmpdir.join('theme').join('templates').mkdir()
    conf = tmpdir.join('sigal.conf.py')
    conf.write("theme = 'theme'")

    settings = read_settings(str(conf))
    assert settings['theme'] == tmpdir.join('theme')
