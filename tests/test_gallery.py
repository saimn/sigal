# -*- coding:utf-8 -*-

import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA

from sigal.gallery import PathsDb, get_metadata
from sigal.settings import read_settings

CURRENT_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(CURRENT_DIR, 'sample')


class TestPaths(unittest.TestCase):
    "Test the PathsDb class."

    @classmethod
    def setUp(cls):
        """Read the sample config file and build the PathsDb object."""

        default_conf = os.path.join(SAMPLE_DIR, 'sigal.conf.py')
        settings = read_settings(default_conf)
        cls.paths = PathsDb(SAMPLE_DIR, settings['ext_list'])
        cls.paths.build()

    def test_filelist(self):
        paths = self.paths.db

        self.assertItemsEqual(
            paths.keys(),
            ['paths_list', 'skipped_dir', '.', 'dir1', 'dir2', 'dir1/test'])

        self.assertListEqual(paths['paths_list'],
                             ['.', 'dir1', 'dir1/test', 'dir2'])
        self.assertListEqual(paths['skipped_dir'], ['empty'])

        self.assertListEqual(paths['.']['img'], [])
        self.assertItemsEqual(paths['.']['subdir'], ['dir1', 'dir2'])

        self.assertItemsEqual(paths['dir1']['img'], ['test1.jpg', 'test2.jpg'])
        self.assertEqual(paths['dir1']['thumbnail'], u'test1.jpg')
        self.assertEqual(paths['dir1']['title'], u'An example gallery')

    def test_get_thumbnail(self):
        self.assertEqual(self.paths.get_thumbnail('dir1'), u'test1.jpg')
        self.assertEqual(self.paths.get_thumbnail('dir1/test'),
                         u'test2.jpg')


class TestMetadata(unittest.TestCase):
    "Test the Gallery class."

    def test_get_metadata(self):
        m = get_metadata(os.path.join(SAMPLE_DIR, 'dir1'))
        self.assertEqual(m['title'], 'An example gallery')
        self.assertEqual(m['thumbnail'], 'test1.jpg')

        m = get_metadata(os.path.join(SAMPLE_DIR, 'dir1', 'test'))
        self.assertEqual(m['title'], 'Test')


# class TestGallery(unittest.TestCase):
#     "Test the Gallery class."

#     @classmethod
#     def setUp(cls):
#         """Read the sample config file."""

#         default_conf = os.path.join(CURRENT_DIR, 'sample', 'sigal.conf.py')
#         settings = read_settings(default_conf)
#         cls.gal = Gallery(settings, os.path.join(CURRENT_DIR, 'sample'),
#                           os.path.join(CURRENT_DIR, 'output'))
