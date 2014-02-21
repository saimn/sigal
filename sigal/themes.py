# -*- coding: utf-8 -*-

import os

THEMES_PATH = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'themes'))

def get_theme_path(theme):
    if not os.path.exists(theme):
        theme = os.path.join(THEMES_PATH, theme)
        if not os.path.exists(theme):
            raise Exception("Impossible to find the theme %s" % theme)

    return theme

def get_templates_path(theme_path):
    return os.path.join(theme_path, 'templates')
