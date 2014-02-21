# -*- coding: utf-8 -*-

import os
from sigal.themes import get_theme_path, get_templates_path

def test_get_theme_path(tmpdir):
    theme_path = get_theme_path('galleria')
    assert theme_path.endswith('sigal/themes/galleria')
    assert get_templates_path(theme_path) != theme_path
    assert get_templates_path(theme_path).startswith(theme_path)
