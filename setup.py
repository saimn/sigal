import os
import sys
from setuptools import setup, find_packages

if sys.version_info[:2] < (3, 5):
    sys.exit('Sigal supports Python 3.5+ only')

with open('README.rst') as f:
    README = f.read()

# Load package meta from the pkgmeta module without loading the package.
pkgmeta = {}
pkgmeta_file = os.path.join(os.path.dirname(__file__), 'sigal', 'pkgmeta.py')
with open(pkgmeta_file) as f:
    code = compile(f.read(), 'pkgmeta.py', 'exec')
    exec(code, pkgmeta)

setup(
    name='sigal',
    version=pkgmeta['__version__'],
    url=pkgmeta['__url__'],
    license='MIT',
    author=pkgmeta['__author__'],
    author_email='contact@saimon.org',
    description='Simple static gallery generator',
    long_description=README,
    packages=find_packages(exclude=['tests*']),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    python_requires='>=3.5',
    keywords=['gallery', 'static', 'generator', 'image', 'video', 'galleria'],
    install_requires=['blinker', 'click', 'Jinja2', 'Markdown',
                      'Pillow>=4.0.0', 'pilkit'],
    test_requires=['pytest'],
    extras_require={
        'S3': ['boto']
    },
    entry_points={
        'console_scripts': ['sigal = sigal:main']
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Multimedia :: Graphics :: Viewers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
