# -*- coding: utf-8 -*-

import os
import pytest

from sigal.settings import read_settings

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def settings():
    """Read the sample config file."""
    return read_settings(os.path.join(CURRENT_DIR, 'sample', 'sigal.conf.py'))
