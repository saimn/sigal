# -*- coding: utf-8 -*-

import os
import PIL
import pytest
import shutil

from sigal.settings import read_settings

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
BUILD_DIR = os.path.join(CURRENT_DIR, 'sample', '_build')


@pytest.fixture(scope='session', autouse=True)
def remove_build():
    """Ensure that build directory does not exists before each test."""
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)


@pytest.fixture
def settings():
    """Read the sample config file."""
    return read_settings(os.path.join(CURRENT_DIR, 'sample', 'sigal.conf.py'))


def pytest_report_header(config):
    return "project deps: Pillow-{}".format(PIL.PILLOW_VERSION)
