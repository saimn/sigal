#! /usr/bin/env python2
# -*- coding:utf-8 -*-

import os
import unittest

from sigal.settings import read_settings, get_size


class TestSettings(unittest.TestCase):
    "Read a settings file and check that the configuration is well done."

    def setUp(self):
        "Read the sample config file"
        self.path = os.path.abspath(os.path.dirname(__file__))
        default_conf = os.path.join(self.path, 'sample', 'sigal.conf')
        self.settings = read_settings(default_conf)

    def test_get_size(self):
        "Test that image sizes are correctly read"
        self.assertTupleEqual(get_size('640x480'), (640, 480))
        self.assertTupleEqual(get_size('480x640'), (640, 480))
        self.assertTupleEqual(self.settings['img_size'], (640, 480))
        self.assertTupleEqual(self.settings['thumb_size'], (200, 150))

    def test_ext_list(self):
        self.assertListEqual(self.settings['ext_list'],
                             ['.jpg', '.jpeg', '.JPG', '.JPEG', '.png'])

    def test_type_conversion(self):
        self.assertEqual(self.settings['jpg_quality'], 90)
