# -*- coding: utf-8 -*-

import blinker
import io
import logging
import os
from click.testing import CliRunner
from os.path import join

from sigal import init, build, serve, set_meta, signals

TESTGAL = join(os.path.abspath(os.path.dirname(__file__)), 'sample')


def test_init(tmpdir):
    config_file = str(tmpdir.join('sigal.conf.py'))
    runner = CliRunner()
    result = runner.invoke(init, [config_file])
    assert result.exit_code == 0
    assert result.output.startswith('Sample config file created:')
    assert os.path.isfile(config_file)

    result = runner.invoke(init, [config_file])
    assert result.exit_code == 1
    assert result.output == ("Found an existing config file, will abort to "
                             "keep it safe.\n")


def test_build(tmpdir):
    runner = CliRunner()
    config_file = str(tmpdir.join('sigal.conf.py'))
    tmpdir.mkdir('pictures')
    tmpdir = str(tmpdir)
    cwd = os.getcwd()

    try:
        result = runner.invoke(init, [config_file])
        assert result.exit_code == 0
        os.symlink(join(TESTGAL, 'watermark.png'),
                   join(tmpdir, 'watermark.png'))
        os.symlink(join(TESTGAL, 'pictures', 'dir2', 'exo20101028-b-full.jpg'),
                   join(tmpdir, 'pictures', 'exo20101028-b-full.jpg'))

        result = runner.invoke(build, ['-n', 1, '--debug'])
        assert result.exit_code == 1

        os.chdir(tmpdir)

        result = runner.invoke(build, ['foo', '-n', 1, '--debug'])
        assert result.exit_code == 1

        result = runner.invoke(build, ['pictures', 'pictures/out',
                                       '-n', 1, '--debug'])
        assert result.exit_code == 1

        with io.open(config_file) as f:
            text = f.read()

        text += """
theme = 'colorbox'
plugins = ['sigal.plugins.adjust', 'sigal.plugins.copyright',
           'sigal.plugins.watermark', 'sigal.plugins.feeds',
           'sigal.plugins.media_page' 'sigal.plugins.nomedia',
           'sigal.plugins.extended_caching']
copyright = "An example copyright message"
copyright_text_font = "foobar"
watermark = "watermark.png"
watermark_position = "scale"
watermark_opacity = 0.3
"""

        with io.open(config_file, 'w') as f:
            f.write(text)

        result = runner.invoke(build, ['pictures', 'build',
                                       '-n', 1, '--debug'])
        assert result.exit_code == 0
        assert os.path.isfile(join(tmpdir, 'build', 'thumbnails',
                                   'exo20101028-b-full.jpg'))
    finally:
        os.chdir(cwd)
        # Reset logger
        logger = logging.getLogger('sigal')
        logger.handlers[:] = []
        logger.setLevel(logging.INFO)
        # Reset plugins
        for name in dir(signals):
            if not name.startswith('_'):
                try:
                    sig = getattr(signals, name)
                    if isinstance(sig, blinker.Signal):
                        sig.receivers.clear()
                except Exception:
                    pass


def test_serve(tmpdir):
    config_file = str(tmpdir.join('sigal.conf.py'))
    runner = CliRunner()
    result = runner.invoke(init, [config_file])
    assert result.exit_code == 0

    result = runner.invoke(serve)
    assert result.exit_code == 2

    result = runner.invoke(serve, ['-c', config_file])
    assert result.exit_code == 1


def test_set_meta(tmpdir):

    testdir = tmpdir.mkdir("test")

    testfile = tmpdir.join("test.jpg")
    testfile.write("")

    runner = CliRunner()
    result = runner.invoke(set_meta, [str(testdir), "title", "testing"])

    assert result.exit_code == 0
    assert result.output.startswith("1 metadata key(s) written to")
    assert os.path.isfile(str(testdir.join("index.md")))
    assert testdir.join("index.md").read() == "Title: testing\n"

    # Run again, should give file exists error
    result = runner.invoke(set_meta, [str(testdir), "title", "testing"])
    assert result.exit_code == 2

    result = runner.invoke(set_meta, [str(testdir.join("non-existant.jpg")),
                                      "title", "testing"])
    assert result.exit_code == 1

    result = runner.invoke(set_meta, [str(testfile), "title", "testing"])

    assert result.exit_code == 0
    assert result.output.startswith("1 metadata key(s) written to")
    assert os.path.isfile(str(tmpdir.join("test.md")))
    assert tmpdir.join("test.md").read() == "Title: testing\n"
