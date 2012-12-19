# -*- coding:utf-8 -*-

import sys
from setuptools import setup, find_packages

requires = ['PIL', 'jinja2', 'Markdown', 'clint']
if sys.version_info < (2, 7):
    requires.append('argparse')

entry_points = {
    'console_scripts': ['sigal = sigal:main']
}

with open('README.rst') as f:
    README = f.read()

setup(
    name='sigal',
    version='0.2',
    url='https://github.com/saimn/sigal',
    license='MIT',
    author='Simon Conseil',
    author_email='contact@saimon.org',
    description='Simple static gallery generator',
    long_description=README,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=requires,
    test_requires=['nose'],
    test_suite='nose.collector',
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
