# -*- coding:utf-8 -*-

import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA

from sigal.settings import read_settings, get_thumb


class TestSettings(unittest.TestCase):
    "Read a settings file and check that the configuration is well done."

    def setUp(self):
        "Read the sample config file"
        self.path = os.path.abspath(os.path.dirname(__file__))
        default_conf = os.path.join(self.path, 'sample', 'sigal.conf.py')
        self.settings = read_settings(default_conf)

    def test_sizes(self):
        "Test that image sizes are correctly read"
        self.assertTupleEqual(self.settings['img_size'], (640, 480))
        self.assertTupleEqual(self.settings['thumb_size'], (200, 150))

    def test_settings(self):
        self.assertEqual(self.settings['thumb_suffix'], '.tn')

    def test_thumb(self):
        """Test the get_thumb function."""

        tests = [('example.jpg', 'thumbnails/example.tn.jpg'),
                 ('test/example.jpg', 'test/thumbnails/example.tn.jpg'),
                 ('test/t/example.jpg', 'test/t/thumbnails/example.tn.jpg')]
        for src, ref in tests:
            self.assertEqual(get_thumb(self.settings, src), ref)
