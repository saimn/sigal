# -*- coding:utf-8 -*-

from setuptools import setup, find_packages
import sys

requires = ['PIL', 'jinja2', 'Markdown', 'clint']
if sys.version_info < (2, 7):
    requires.append('argparse')

entry_points = {
    'console_scripts': ['sigal = sigal:main']
}

setup(
    name='sigal',
    version='0.1-dev',
    url='https://github.com/saimn/sigal',
    license='MIT',
    author='Simon Conseil',
    author_email='contact@saimon.org',
    description='Simple static gallery generator',
    long_description=open('README.rst').read(),
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=requires,
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
