#! /usr/bin/env python2
# -*- coding:utf-8 -*-

import os
import unittest

from sigal.gallery import Gallery
from sigal.settings import read_settings


class TestGallery(unittest.TestCase):
    "Test the Gallery class."

    def setUp(self):
        "Read the sample config file"
        self.path = os.path.dirname(__file__)
        default_conf = os.path.join(self.path, 'sample', 'sigal.conf')
        settings = read_settings(default_conf)
        self.gallery = Gallery(settings, os.path.join(self.path, 'sample'),
                               os.path.join(self.path, 'output'))

    def test_filelist(self):
        file_generator = self.gallery.filelist()
        dirpath, dirnames, imglist = file_generator.next()
        self.assertEqual(dirpath, os.path.join(self.path, 'sample'))
        self.assertListEqual(imglist, [])

        reflist = [os.path.join(self.path, 'sample', 'dir2', f)
                   for f in ['test1.jpg', 'test2.jpg']]
        dirpath, dirnames, imglist = file_generator.next()
        self.assertItemsEqual(imglist, reflist)
