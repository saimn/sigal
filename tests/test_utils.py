# -*- coding: utf-8 -*-

import os
from sigal.utils import copy

CURRENT_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(CURRENT_DIR, 'sample')


def test_copy(tmpdir):
    filename = 'exo20101028-b-full.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    dst = str(tmpdir.join(filename))
    copy(src, dst)
    assert os.path.isfile(dst)

    filename = 'm57_the_ring_nebula-587px.jpg'
    src = os.path.join(SAMPLE_DIR, 'pictures', 'dir2', filename)
    dst = str(tmpdir.join(filename))
    copy(src, dst, symlink=True)
    assert os.path.islink(dst)
