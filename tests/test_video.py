import os

import pytest

from sigal.gallery import Video
from sigal.settings import Status, create_settings
from sigal.video import (generate_thumbnail, generate_video, process_video,
                         video_size, get_resize_options, generate_video_pass)
from unittest.mock import patch

CURRENT_DIR = os.path.dirname(__file__)
SRCDIR = os.path.join(CURRENT_DIR, 'sample', 'pictures')
TEST_VIDEO = 'example video.ogv'
SRCFILE = os.path.join(SRCDIR, 'video', TEST_VIDEO)


def test_video_size():
    size_src = video_size(SRCFILE)
    assert size_src == (320, 240)
    size_src = video_size('missing/file.mp4')
    assert size_src == (0, 0)


def test_generate_thumbnail(tmpdir):
    outname = str(tmpdir.join('test.jpg'))
    generate_thumbnail(SRCFILE, outname, (50, 50), 5)
    assert os.path.isfile(outname)


def test_process_video(tmpdir):
    base, ext = os.path.splitext(TEST_VIDEO)

    settings = create_settings(video_format='ogv',
                               use_orig=True, orig_link=True,
                               source=os.path.join(SRCDIR, 'video'),
                               destination=str(tmpdir))
    video = Video(TEST_VIDEO, '.', settings)
    process_video(video)
    dstfile = str(tmpdir.join(base + '.ogv'))
    assert os.path.realpath(dstfile) == SRCFILE

    settings = create_settings(video_format='mjpg')
    assert process_video(video) == Status.FAILURE

    settings = create_settings(thumb_video_delay=-1)
    assert process_video(video) == Status.FAILURE


@pytest.mark.parametrize("fmt", ['webm', 'mp4'])
def test_generate_video_fit_height(tmpdir, fmt):
    """largest fitting dimension is height"""

    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.' + fmt))
    settings = create_settings(video_size=(80, 100), video_format=fmt)
    generate_video(SRCFILE, dstfile, settings)

    size_src = video_size(SRCFILE)
    size_dst = video_size(dstfile)

    assert size_dst[0] == 80
    # less than 2% error on ratio
    assert abs(size_dst[0] / size_dst[1] - size_src[0] / size_src[1]) < 2e-2


@pytest.mark.parametrize("fmt", ['webm', 'mp4'])
def test_generate_video_fit_width(tmpdir, fmt):
    """largest fitting dimension is width"""

    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.' + fmt))
    settings = create_settings(video_size=(100, 50), video_format=fmt)
    generate_video(SRCFILE, dstfile, settings)

    size_src = video_size(SRCFILE)
    size_dst = video_size(dstfile)

    assert size_dst[1] == 50
    # less than 2% error on ratio
    assert abs(size_dst[0] / size_dst[1] - size_src[0] / size_src[1]) < 2e-2


@pytest.mark.parametrize("fmt", ['webm', 'mp4', 'ogv'])
def test_generate_video_dont_enlarge(tmpdir, fmt):
    """Video dimensions should not be enlarged."""

    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.' + fmt))
    settings = create_settings(video_size=(1000, 1000), video_format=fmt)
    generate_video(SRCFILE, dstfile, settings)
    size_src = video_size(SRCFILE)
    size_dst = video_size(dstfile)

    assert size_src == size_dst


@patch('sigal.video.generate_video_pass')
@pytest.mark.parametrize("fmt", ['webm', 'mp4'])
def test_second_pass_video(mock_generate_video_pass, fmt, tmpdir):
    """Video should be run through ffmpeg."""
    base, ext = os.path.splitext(TEST_VIDEO)
    dstfile = str(tmpdir.join(base + '.' + fmt))
    settings_1 = '-c:v libvpx-vp9 -b:v 0 -crf 30 -pass 1 -an -f null dev/null'
    settings_2 = '-c:v libvpx-vp9 -b:v 0 -crf 30 -pass 2 -f {}'.format(fmt)
    settings_opts = {'video_size': (100, 50), 'video_format': fmt,
                     fmt + '_options': settings_1.split(" "),
                     fmt + '_options_second_pass': settings_2.split(" ")}

    settings = create_settings(**settings_opts)
    generate_video(SRCFILE, dstfile, settings)
    call_args_list = mock_generate_video_pass.call_args_list
    # The method is called twice
    assert len(call_args_list) == 2
    # The first call to the method should have 3 args, without the outname
    args, kwargs = call_args_list[0]
    assert len(args) == 3
    # The second call to the method should have 4 args, with the outname
    args, kwargs = call_args_list[1]
    assert len(args) == 4
