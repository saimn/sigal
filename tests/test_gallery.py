#! /usr/bin/env python2
# -*- coding:utf-8 -*-

import os
import unittest

from sigal.gallery import Gallery
from sigal.settings import read_settings

CURRENT_DIR = os.path.dirname(__file__)


class TestGallery(unittest.TestCase):
    "Test the Gallery class."

    def setUp(self):
        """Read the sample config file."""

        default_conf = os.path.join(CURRENT_DIR, 'sample', 'sigal.conf')
        settings = read_settings(default_conf)
        self.gal = Gallery(settings, os.path.join(CURRENT_DIR, 'sample'),
                           os.path.join(CURRENT_DIR, 'output'))

    def test_filelist(self):
        self.gal.build_paths()
        paths = self.gal.paths

        self.assertItemsEqual(paths.keys(), ['.', 'dir1', 'dir2'])

        self.assertListEqual(paths['.']['img'], [])
        self.assertItemsEqual(paths['.']['subdir'], ['dir1', 'dir2'])

        self.assertItemsEqual(paths['dir1']['img'], ['test1.jpg', 'test2.jpg'])
        self.assertEqual(paths['dir1']['representative'], u'test1.jpg')
        self.assertEqual(paths['dir1']['title'], u'An example gallery')
