# -*- coding:utf-8 -*-

import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA

from sigal.gallery import Gallery, get_metadata
from sigal.settings import read_settings

CURRENT_DIR = os.path.dirname(__file__)


class TestGallery(unittest.TestCase):
    "Test the Gallery class."

    @classmethod
    def setUp(cls):
        """Read the sample config file."""

        default_conf = os.path.join(CURRENT_DIR, 'sample', 'sigal.conf.py')
        settings = read_settings(default_conf)
        cls.gal = Gallery(settings, os.path.join(CURRENT_DIR, 'sample'),
                          os.path.join(CURRENT_DIR, 'output'))
        cls.gal.build_paths()

    def test_filelist(self):
        paths = self.gal.paths

        self.assertItemsEqual(paths.keys(),
                              ['paths_list', '.', 'dir1', 'dir2', 'dir1/test'])
        self.assertListEqual(paths['paths_list'],
                             ['.', 'dir1', 'dir1/test', 'dir2'])

        self.assertListEqual(paths['.']['img'], [])
        self.assertItemsEqual(paths['.']['subdir'], ['dir1', 'dir2'])

        self.assertItemsEqual(paths['dir1']['img'], ['test1.jpg', 'test2.jpg'])
        self.assertEqual(paths['dir1']['representative'], u'test1.jpg')
        self.assertEqual(paths['dir1']['title'], u'An example gallery')

    def test_find_representative(self):
        self.assertEqual(self.gal.find_representative('dir1'), u'test1.jpg')
        self.assertEqual(self.gal.find_representative('dir1/test'),
                         u'test2.jpg')


class TestMetadata(unittest.TestCase):
    "Test the Gallery class."

    def test_get_metadata(self):
        m = get_metadata(os.path.join(CURRENT_DIR, 'sample', 'dir1'))
        self.assertEqual(m['title'], 'An example gallery')
        self.assertEqual(m['representative'], 'test1.jpg')

        m = get_metadata(os.path.join(CURRENT_DIR, 'sample', 'dir1', 'test'))
        self.assertEqual(m['title'], 'Test')
