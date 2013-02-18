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

REF = {
    'dir1': {
        'title': 'An example gallery',
        'thumbnail': 'test1/11.jpg',
        'img': '',
    },
    'dir1/test1': {
        'title': 'Test1',
        'thumbnail': '11.jpg',
        'img': ['11.jpg'],
    },
    'dir1/test2': {
        'title': 'Test2',
        'thumbnail': '21.jpg',
        'img': ['21.jpg', '22.jpg'],
    },
    'dir2': {
        'title': 'Another example gallery',
        'thumbnail': 'm57_the_ring_nebula-587px.jpg',
        'img': ['exo20101028-b-full.jpg',
                'm57_the_ring_nebula-587px.jpg',
                'Hubble ultra deep field.jpg',
                'Hubble Interacting Galaxy NGC 5257.jpg']
    }
}


class TestPathsDb(unittest.TestCase):
    "Test the PathsDb class."

    @classmethod
    def setUp(cls):
        """Read the sample config file and build the PathsDb object."""

        default_conf = os.path.join(SAMPLE_DIR, 'sigal.conf.py')
        settings = read_settings(default_conf)
        cls.paths = PathsDb(SAMPLE_DIR, settings['ext_list'])
        cls.paths.build()
        cls.db = cls.paths.db

    def test_filelist(self):
        self.assertItemsEqual(self.db.keys(),
                              ['paths_list', 'skipped_dir', '.', 'dir1',
                               'dir2', 'dir1/test1', 'dir1/test2'])

        self.assertListEqual(self.db['paths_list'],
                             ['.', 'dir1', 'dir1/test1', 'dir1/test2', 'dir2'])
        self.assertListEqual(self.db['skipped_dir'], ['empty'])

        self.assertListEqual(self.db['.']['img'], [])
        self.assertItemsEqual(self.db['.']['subdir'], ['dir1', 'dir2'])

    def test_title(self):
        for p in REF.keys():
            self.assertEqual(self.db[p]['title'], REF[p]['title'])

    def test_thumbnail(self):
        for p in REF.keys():
            self.assertEqual(self.db[p]['thumbnail'], REF[p]['thumbnail'])

    def test_imglist(self):
        for p in REF.keys():
            self.assertItemsEqual(self.db[p]['img'], REF[p]['img'])


class TestMetadata(unittest.TestCase):
    "Test the Gallery class."

    def test_dir1(self):
        m = get_metadata(os.path.join(SAMPLE_DIR, 'dir1'))
        self.assertEqual(m['title'], REF['dir1']['title'])
        self.assertEqual(m['thumbnail'], '')

    def test_dir2(self):
        m = get_metadata(os.path.join(SAMPLE_DIR, 'dir2'))
        self.assertEqual(m['title'], REF['dir2']['title'])
        self.assertEqual(m['thumbnail'], REF['dir2']['thumbnail'])


# class TestGallery(unittest.TestCase):
#     "Test the Gallery class."

#     @classmethod
#     def setUp(cls):
#         """Read the sample config file."""

#         default_conf = os.path.join(CURRENT_DIR, 'sample', 'sigal.conf.py')
#         settings = read_settings(default_conf)
#         cls.gal = Gallery(settings, os.path.join(CURRENT_DIR, 'sample'),
#                           os.path.join(CURRENT_DIR, 'output'))
