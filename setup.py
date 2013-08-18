# -*- coding:utf-8 -*-

import os
from setuptools import setup

requires = ['argh', 'clint', 'jinja2', 'Markdown', 'pilkit']

try:
    from PIL import Image, ImageOps  # NOQA
except ImportError:
    requires += ['Pillow']

entry_points = {
    'console_scripts': ['sigal = sigal:main']
}

with open('README.rst') as f:
    README = f.read()

with open('docs/changelog.rst') as f:
    CHANGELOG = f.read()

# Load package meta from the pkgmeta module without loading the package.
pkgmeta = {}
execfile(os.path.join(os.path.dirname(__file__), 'sigal', 'pkgmeta.py'),
         pkgmeta)

setup(
    name='sigal',
    version=pkgmeta['__version__'],
    url=pkgmeta['__url__'],
    license='MIT',
    author=pkgmeta['__author__'],
    author_email='contact@saimon.org',
    description='Simple static gallery generator',
    long_description=README + '\n' + CHANGELOG,
    packages=['sigal'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=requires,
    test_requires=['pytest'],
    entry_points=entry_points,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Multimedia :: Graphics :: Viewers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
