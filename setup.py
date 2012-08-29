#!/usr/bin/env python2
# -*- coding:utf-8 -*-

from setuptools import setup
import sys

requires = ['PIL', 'jinja2', 'Markdown']
if sys.version_info < (2,7):
    requires.append('argparse')

entry_points = {
    'console_scripts':
        ['sigal = sigal:main']
    }

setup(
    name = 'sigal',
    version = '0.1-dev',
    description = 'simple static gallery generator',
    long_description = open('README.rst').read(),
    url = 'https://github.com/saimn/sigal',
    author = 'Simon C.',
    author_email = 'contact@saimon.org',
    license = 'MIT',
    include_package_data = True,
    install_requires  =  requires,
    entry_points = entry_points,
    packages = ['sigal'],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Internet :: WWW/HTTP',
                   'Topic :: Multimedia :: Graphics :: Viewers',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   ],
    )
