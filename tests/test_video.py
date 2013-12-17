# -*- coding:utf-8 -*-

from __future__ import division

import os

from sigal.video import video_size, generate_video

CURRENT_DIR = os.path.dirname(__file__)
TEST_VIDEO = 'stallman-software-freedom-day-low.ogv'
SRCFILE = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'video', TEST_VIDEO)


def test_generate_video_fit_height(tmpdir):
    """largest fitting dimension is height"""

    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.webm'))
    generate_video(SRCFILE, dstfile, (50, 100))

    size_src = video_size(SRCFILE)
    size_dst = video_size(dstfile)

    assert size_dst[0] == 50
    # less than 2% error on ratio
    assert abs(size_dst[0]/size_dst[1] - size_src[0]/size_src[1]) < 2e-2


def test_generate_video_fit_width(tmpdir):
    """largest fitting dimension is width"""

    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.webm'))
    generate_video(SRCFILE, dstfile, (100, 50))

    size_src = video_size(SRCFILE)
    size_dst = video_size(dstfile)

    assert size_dst[1] == 50
    # less than 2% error on ratio
    assert abs(size_dst[0]/size_dst[1] - size_src[0]/size_src[1]) < 2e-2


def test_generate_video_dont_enlarge(tmpdir):
    """video dimensions should not be enlarged"""

    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.webm'))
    generate_video(SRCFILE, dstfile, (1000, 1000))

    size_src = video_size(SRCFILE)
    size_dst = video_size(dstfile)

    assert size_src == size_dst
