# -*- coding:utf-8 -*-

import os

from sigal.image import generate_image, generate_thumbnail

CURRENT_DIR = os.path.dirname(__file__)
TEST_IMAGE = 'exo20101028-b-full.jpg'


def test_image(tmpdir):
    "Test the Image class."

    srcfile = os.path.join(CURRENT_DIR, 'sample', 'dir2', TEST_IMAGE)
    dstfile = str(tmpdir.join(TEST_IMAGE))

    generate_thumbnail(srcfile, dstfile, (200, 150))
    assert os.path.isfile(dstfile)
