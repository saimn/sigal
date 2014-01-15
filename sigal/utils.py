# -*- coding: utf-8 -*-

import os
import shutil


def copy(src, dst, symlink=False):
    """Copy or symlink the file."""
    func = os.symlink if symlink else shutil.copy2
    if symlink and os.path.lexists(dst):
        os.remove(dst)
    func(src, dst)
