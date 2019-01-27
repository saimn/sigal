import sys
from setuptools import setup

if sys.version_info[:2] < (3, 5):
    sys.exit('Sigal supports Python 3.5+ only')

setup()
