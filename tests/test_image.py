import os
import PIL
import pytest
from unittest.mock import Mock, patch
from PIL import Image

from sigal import init_logging
from sigal.image import (generate_image, generate_thumbnail, get_exif_tags,
                         get_exif_data, get_size, process_image, get_iptc_data)
from sigal.settings import create_settings, Status

CURRENT_DIR = os.path.dirname(__file__)
TEST_IMAGE = 'KeckObservatory20071020.jpg'
SRCFILE = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir2', TEST_IMAGE)

TEST_GIF_IMAGE = 'example.gif'
SRC_GIF_FILE = os.path.join(CURRENT_DIR, 'sample', 'pictures',
                            'dir1', 'test1', TEST_GIF_IMAGE)


def test_process_image(tmpdir):
    "Test the process_image function."

    status = process_image('foo.txt', 'none.txt', {})
    assert status == Status.FAILURE

    settings = create_settings(img_processor='ResizeToFill', make_thumbs=False)
    status = process_image(SRCFILE, str(tmpdir), settings)
    assert status == Status.SUCCESS
    im = Image.open(os.path.join(str(tmpdir), TEST_IMAGE))
    assert im.size == settings['img_size']


def test_generate_image(tmpdir):
    "Test the generate_image function."

    dstfile = str(tmpdir.join(TEST_IMAGE))
    for i, size in enumerate([(600, 600), (300, 200)]):
        settings = create_settings(img_size=size, img_processor='ResizeToFill',
                                   copy_exif_data=True)
        options = None if i == 0 else {'quality': 85}
        generate_image(SRCFILE, dstfile, settings, options=options)
        im = Image.open(dstfile)
        assert im.size == size


def test_resize_image_portrait(tmpdir):
    """Test that the area is the same regardless of aspect ratio."""
    size = (300, 200)
    settings = create_settings(img_size=size)

    portrait_image = 'm57_the_ring_nebula-587px.jpg'
    portrait_src = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir2', portrait_image)
    portrait_dst = str(tmpdir.join(portrait_image))

    generate_image(portrait_src, portrait_dst, settings)
    im = Image.open(portrait_dst)

    # In the default mode, PILKit resizes in a way to never make an image
    # smaller than either of the lengths, the other is scaled accordingly.
    # Hence we test that the shorter side has the smallest length.
    assert im.size[0] == 200

    landscape_image = 'KeckObservatory20071020.jpg'
    landscape_src = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir2', landscape_image)
    landscape_dst = str(tmpdir.join(landscape_image))

    generate_image(landscape_src, landscape_dst, settings)
    im = Image.open(landscape_dst)
    assert im.size[1] == 200


@pytest.mark.parametrize(("image", "path"), [(TEST_IMAGE, SRCFILE),
                                             (TEST_GIF_IMAGE, SRC_GIF_FILE)])
def test_generate_image_passthrough(tmpdir, image, path):
    "Test the generate_image function with use_orig=True."

    dstfile = str(tmpdir.join(image))
    settings = create_settings(use_orig=True)
    generate_image(path, dstfile, settings)
    # Check the file was copied, not (sym)linked
    st_src = os.stat(path)
    st_dst = os.stat(dstfile)
    assert st_src.st_size == st_dst.st_size
    assert not os.path.samestat(st_src, st_dst)


def test_generate_image_passthrough_symlink(tmpdir):
    "Test the generate_image function with use_orig=True and orig_link=True."

    dstfile = str(tmpdir.join(TEST_IMAGE))
    settings = create_settings(use_orig=True, orig_link=True)
    generate_image(SRCFILE, dstfile, settings)
    # Check the file was symlinked
    assert os.path.islink(dstfile)
    assert os.path.samefile(SRCFILE, dstfile)


def test_generate_image_processor(tmpdir):
    "Test generate_image with a wrong processor name."

    init_logging('sigal')
    dstfile = str(tmpdir.join(TEST_IMAGE))
    settings = create_settings(img_size=(200, 200),
                               img_processor='WrongMethod')

    with pytest.raises(SystemExit):
        generate_image(SRCFILE, dstfile, settings)


@pytest.mark.parametrize(
    ("image", "path", "wide_size", "high_size"),
    [(TEST_IMAGE, SRCFILE, (200, 133), (150, 100)),
     (TEST_GIF_IMAGE, SRC_GIF_FILE, (134, 150), (150, 168))])
def test_generate_thumbnail(tmpdir, image, path, wide_size, high_size):
    "Test the generate_thumbnail function."

    dstfile = str(tmpdir.join(image))
    for size in [(200, 150), (150, 200)]:
        generate_thumbnail(path, dstfile, size)
        im = Image.open(dstfile)
        assert im.size == size

    for size, thumb_size in [((200, 150), wide_size),
                             ((150, 200), high_size)]:
        generate_thumbnail(path, dstfile, size, fit=False)
        im = Image.open(dstfile)
        assert im.size == thumb_size


def test_get_exif_tags():
    test_image = '11.jpg'
    src_file = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir1', 'test1',
                            test_image)
    data = get_exif_data(src_file)
    simple = get_exif_tags(data, datetime_format='%d/%m/%Y')
    assert simple['fstop'] == 3.9
    assert simple['focal'] == 12.0
    assert simple['iso'] == 50
    assert simple['Make'] == 'NIKON'
    assert simple['datetime'] == '22/01/2006'
    if PIL.__version__ == '3.0.0':
        assert simple['exposure'] == 0.00100603
    else:
        assert simple['exposure'] == '100603/100000000'

    data = {'FNumber': [1, 0], 'FocalLength': [1, 0], 'ExposureTime': 10}
    simple = get_exif_tags(data)
    assert 'fstop' not in simple
    assert 'focal' not in simple
    assert simple['exposure'] == '10'

    data = {'ExposureTime': '--', 'DateTimeOriginal': '---',
            'GPSInfo': {'GPSLatitude': ((34, 0), (1, 0), (4500, 100)),
                        'GPSLatitudeRef': 'N',
                        'GPSLongitude': ((116, 0), (8, 0), (3900, 100)),
                        'GPSLongitudeRef': 'W'}}
    simple = get_exif_tags(data)
    assert 'exposure' not in simple
    assert 'datetime' not in simple
    assert 'gps' not in simple


def test_get_iptc_data(caplog):
    test_image = '1.jpg'
    src_file = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'iptcTest',
                            test_image)
    data = get_iptc_data(src_file)
    # Title
    assert data["title"] == 'Haemostratulus clouds over Canberra - ' + \
            '2005-12-28 at 03-25-07'
    # Description
    assert data["description"] == '"Haemo" because they look like haemoglobin ' + \
            'cells and "stratulus" because I can\'t work out whether ' + \
            'they\'re Stratus or Cumulus clouds.\nWe\'re driving down ' + \
            'the main drag in Canberra so it\'s Parliament House that ' + \
            'you can see at the end of the road.'
    # This file has no IPTC data
    test_image = '21.jpg'
    src_file = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'exifTest',
                            test_image)
    assert get_iptc_data(src_file) == {}

    # Headline
    test_image = '3.jpg'
    src_file = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'iptcTest',
                            test_image)
    data = get_iptc_data(src_file)
    assert data["headline"] == 'Ring Nebula, M57'

    # Test catching the SyntaxError -- assert output
    with patch('sigal.image.IptcImagePlugin.getiptcinfo', side_effect=SyntaxError):
            get_iptc_data(src_file)
            assert ['IPTC Error in'] == [ log.message[:13] for log in caplog.records ]


def test_iso_speed_ratings():
    data = {'ISOSpeedRatings': ()}
    simple = get_exif_tags(data)
    assert 'iso' not in simple

    data = {'ISOSpeedRatings': None}
    simple = get_exif_tags(data)
    assert 'iso' not in simple

    data = {'ISOSpeedRatings': 125}
    simple = get_exif_tags(data)
    assert 'iso' in simple


def test_null_exposure_time():
    data = {'ExposureTime': (0, 0)}
    simple = get_exif_tags(data)
    assert 'exposure' not in simple


def test_exif_copy(tmpdir):
    "Test if EXIF data can transferred copied to the resized image."

    test_image = '11.jpg'
    src_file = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir1', 'test1',
                            test_image)
    dst_file = str(tmpdir.join(test_image))

    settings = create_settings(img_size=(300, 400), copy_exif_data=True)
    generate_image(src_file, dst_file, settings)
    simple = get_exif_tags(get_exif_data(dst_file))
    assert simple['iso'] == 50

    settings['copy_exif_data'] = False
    generate_image(src_file, dst_file, settings)
    simple = get_exif_tags(get_exif_data(dst_file))
    assert not simple


@pytest.mark.xfail(PIL.__version__ == '3.0.0',
                   reason="Pillow 3.0.0 was broken")
def test_exif_gps(tmpdir):
    """Test reading out correct geo tags"""

    test_image = 'flickr_jerquiaga_2394751088_cc-by-nc.jpg'
    src_file = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir1', 'test1',
                            test_image)
    dst_file = str(tmpdir.join(test_image))

    settings = create_settings(img_size=(400, 300), copy_exif_data=True)
    generate_image(src_file, dst_file, settings)
    simple = get_exif_tags(get_exif_data(dst_file))
    assert 'gps' in simple

    lat = 34.029167
    lon = -116.144167

    assert abs(simple['gps']['lat'] - lat) < 0.0001
    assert abs(simple['gps']['lon'] - lon) < 0.0001


def test_get_size(tmpdir):
    """Test reading out image size"""

    test_image = 'flickr_jerquiaga_2394751088_cc-by-nc.jpg'
    src_file = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir1', 'test1',
                            test_image)

    result = get_size(src_file)
    assert result == {'height': 800, 'width': 600}


def test_get_size_with_invalid_path(tmpdir):
    """Test reading out image size with a missing file"""

    test_image = 'missing-file.jpg'
    src_file = os.path.join(CURRENT_DIR, test_image)

    result = get_size(src_file)
    assert result is None
