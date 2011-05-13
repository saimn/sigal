#!/usr/bin/env python2
# -*- coding:utf-8 -*-

from distutils.core import setup
import sys

requires = ['imaging', 'jinja2', 'docutils']
if sys.version_info < (2,7):
    requires.append('argparse')

setup(
    name = 'sigal',
    version = '0.1',
    description = 'simple static gallery generator',
    long_description =
    '''
    sigal is yet another python script to prepare a static gallery of images:

    * resize images, create thumbnails with some options (squared thumbs, ...).
    * generate html pages.
    ''',
    url = 'https://github.com/saimn/sigal',
    author = 'Simon C.',
    author_email = 'contact@saimon.org',
    license = 'GPLv3',
    requires = requires,
    # install_requires  =  requires,
    packages = ['sigal'],
    scripts = ['bin/sigal'],
    )

