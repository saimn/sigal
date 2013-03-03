# -*- coding:utf-8 -*-

import os
from tempfile import mkdtemp
from shutil import rmtree

try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA

from sigal.image import Image

CURRENT_DIR = os.path.dirname(__file__)
TEST_IMAGE = 'exo20101028-b-full.jpg'


class TestImage(unittest.TestCase):
    "Test the Image class."

    def setUp(self):
        self.temp_path = mkdtemp()
        self.srcfile = os.path.join(CURRENT_DIR, 'sample', 'dir2', TEST_IMAGE)
        self.dstfile = os.path.join(self.temp_path, TEST_IMAGE)
        self.img = Image(self.srcfile)

    def tearDown(self):
        rmtree(self.temp_path)

    def test_imgname(self):
        self.assertEqual(self.img.imgname, TEST_IMAGE)

    def test_save(self):
        self.img.save(self.dstfile)
        self.assertTrue(os.path.isfile(self.dstfile))
