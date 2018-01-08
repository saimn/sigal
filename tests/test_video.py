# -*- coding:utf-8 -*-

from __future__ import division

import os
import pytest

from sigal.video import video_size, generate_video, process_video
from sigal.settings import create_settings, Status

CURRENT_DIR = os.path.dirname(__file__)
TEST_VIDEO = 'stallman software-freedom-day-low.ogv'
SRCFILE = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'video', TEST_VIDEO)


def test_video_size():
    size_src = video_size(SRCFILE)
    assert size_src == (480, 270)
    size_src = video_size('missing/file.mp4')
    assert size_src == (0, 0)


def test_process_video(tmpdir):
    base, ext = os.path.splitext(TEST_VIDEO)

    settings = create_settings(video_format='ogv', use_orig=True,
                               orig_link=True)
    process_video(SRCFILE, str(tmpdir), settings)
    dstfile = str(tmpdir.join(base + '.ogv'))
    assert os.path.realpath(dstfile) == SRCFILE

    settings = create_settings(video_format='mjpg')
    assert process_video(SRCFILE, str(tmpdir), settings) == Status.FAILURE

    settings = create_settings(thumb_video_delay=-1)
    assert process_video(SRCFILE, str(tmpdir), settings) == Status.FAILURE


@pytest.mark.parametrize("fmt", ['webm', 'mp4'])
def test_generate_video_fit_height(tmpdir, fmt):
    """largest fitting dimension is height"""

    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.' + fmt))
    settings = create_settings(video_size=(50, 100), video_format=fmt)
    generate_video(SRCFILE, dstfile, settings,
                   options=settings[fmt + '_options'])

    size_src = video_size(SRCFILE)
    size_dst = video_size(dstfile)

    assert size_dst[0] == 50
    # less than 2% error on ratio
    assert abs(size_dst[0]/size_dst[1] - size_src[0]/size_src[1]) < 2e-2


@pytest.mark.parametrize("fmt", ['webm', 'mp4'])
def test_generate_video_fit_width(tmpdir, fmt):
    """largest fitting dimension is width"""

    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.' + fmt))
    settings = create_settings(video_size=(100, 50), video_format=fmt)
    generate_video(SRCFILE, dstfile, settings,
                   options=settings[fmt + '_options'])

    size_src = video_size(SRCFILE)
    size_dst = video_size(dstfile)

    assert size_dst[1] == 50
    # less than 2% error on ratio
    assert abs(size_dst[0]/size_dst[1] - size_src[0]/size_src[1]) < 2e-2


@pytest.mark.parametrize("fmt", ['webm', 'mp4', 'ogv'])
def test_generate_video_dont_enlarge(tmpdir, fmt):
    """video dimensions should not be enlarged"""

    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.' + fmt))
    settings = create_settings(video_size=(1000, 1000), video_format=fmt)
    generate_video(SRCFILE, dstfile, settings,
                   options=settings.get(fmt + '_options'))
    size_src = video_size(SRCFILE)
    size_dst = video_size(dstfile)

    assert size_src == size_dst


def test_generate_video_works_with_spaces(tmpdir):
    """video file should be able to live in folders with spaces in their name"""

    test_folder = os.path.join(CURRENT_DIR, 'sample', 'pictures', 'space video')
    srcfile = os.path.join(test_folder, 'Apollo13 Houston Weve Got A Problem.webm')
    dstfile = str(tmpdir.join('space video', 'Apollo13 Houston Weve Got A Problem.ogv'))
    os.mkdir(os.path.dirname(dstfile))
    settings = create_settings(video_format='ogv')
    generate_video(srcfile, dstfile, settings)

    assert os.path.exists(dstfile)
