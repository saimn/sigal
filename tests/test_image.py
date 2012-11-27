# -*- coding:utf-8 -*-

import os
from tempfile import mkdtemp
from shutil import rmtree

try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA

try:
    import pyexiv2
except ImportError:
    pyexiv2 = False

from sigal.image import copy_exif, Image

CURRENT_DIR = os.path.dirname(__file__)


@unittest.skipUnless(pyexiv2, "pyexiv2 isn't installed")
class TestExif(unittest.TestCase):
    "Test the copy of exif metadata with pyexiv2."

    def setUp(self):
        self.temp_path = mkdtemp()
        self.srcfile = os.path.join(CURRENT_DIR,
                                    'sample/dir2/exo20101028-b-full.jpg')
        self.dstfile = os.path.join(self.temp_path, 'exo20101028-b-full.jpg')

        img = Image(self.srcfile)
        img.save(self.dstfile)
        copy_exif(self.srcfile, self.dstfile)

    def tearDown(self):
        rmtree(self.temp_path)

    def test_exif(self):
        src = pyexiv2.ImageMetadata(self.srcfile)
        dst = pyexiv2.ImageMetadata(self.dstfile)
        src.read()
        dst.read()

        self.assertListEqual(src.keys(), dst.keys())
