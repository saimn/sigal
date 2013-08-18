# -*- coding:utf-8 -*-

import os
import pytest
from PIL import Image

from sigal import init_logging
from sigal.image import generate_image, generate_thumbnail, get_exif_tags
from sigal.settings import create_settings

CURRENT_DIR = os.path.dirname(__file__)
TEST_IMAGE = 'exo20101028-b-full.jpg'
SRCFILE = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir2', TEST_IMAGE)


def test_generate_image(tmpdir):
    "Test the generate_image function."

    dstfile = str(tmpdir.join(TEST_IMAGE))
    for size in [(600, 600), (300, 200)]:
        settings = create_settings(img_size=size, img_processor='ResizeToFill')
        generate_image(SRCFILE, dstfile, settings)
        im = Image.open(dstfile)
        assert im.size == size


def test_generate_image_processor(tmpdir):
    "Test generate_image with a wrong processor name."

    init_logging()
    dstfile = str(tmpdir.join(TEST_IMAGE))
    with pytest.raises(SystemExit):
        settings = create_settings(img_size=(200, 200), img_processor='WrongMethod')
        generate_image(SRCFILE, dstfile, settings)


def test_generate_thumbnail(tmpdir):
    "Test the generate_thumbnail function."

    dstfile = str(tmpdir.join(TEST_IMAGE))
    for size in [(200, 150), (150, 200)]:
        generate_thumbnail(SRCFILE, dstfile, size)
        im = Image.open(dstfile)
        assert im.size == size

    for size, thumb_size in [((200, 150), (185, 150)),
                             ((150, 200), (150, 122))]:
        generate_thumbnail(SRCFILE, dstfile, size, fit=False)
        im = Image.open(dstfile)
        assert im.size == thumb_size


def test_exif_copy(tmpdir):
    "Test if EXIF data can transfered copied to the resized image."

    test_image = '11.jpg'
    src_file = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir1', 'test1',
                            test_image)
    dst_file = str(tmpdir.join(test_image))

    settings = create_settings(img_size=(300, 400), copy_exif_data=True)
    generate_image(src_file, dst_file, settings)
    raw, simple = get_exif_tags(dst_file)
    assert simple['iso'] == 50

    settings['copy_exif_data'] = False
    generate_image(src_file, dst_file, settings)
    raw, simple = get_exif_tags(dst_file)
    assert not raw
    assert not simple


def test_exif_gps(tmpdir):
    """Test reading out correct geo tags"""
    test_image = 'flickr_jerquiaga_2394751088_cc-by-nc.jpg'
    src_file = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'dir1', 'test1',
                            test_image)
    dst_file = str(tmpdir.join(test_image))

    settings = create_settings(img_size=(400, 300), copy_exif_data=True)
    generate_image(src_file, dst_file, settings)
    raw, simple = get_exif_tags(dst_file)
    assert 'gps' in simple

    lat = 35.266666
    lon = -117.216666

    assert abs(simple['gps']['lat'] - lat) < 0.0001
    assert abs(simple['gps']['lon'] - lon) < 0.0001
