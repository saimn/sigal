# -*- coding: utf-8 -*-

import os
from sigal import init


def test_init(tmpdir):
    config_file = str(tmpdir.join('sigal.conf.py'))
    init(path=config_file)
    assert os.path.isfile(config_file)
