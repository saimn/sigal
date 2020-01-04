import sys
from setuptools import setup

if sys.version_info[:2] < (3, 6):
    sys.exit('Sigal supports Python 3.6+ only')

setup(use_scm_version=True)
