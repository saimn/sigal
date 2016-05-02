# -*- coding: utf-8 -*-

import os
from click.testing import CliRunner

from sigal import init
from sigal import serve
from sigal import set_meta


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

    result = runner.invoke(set_meta, [str(testdir.join("non-existant.jpg")), "title", "testing"])
    assert result.exit_code == 1

    result = runner.invoke(set_meta, [str(testfile), "title", "testing"])

    assert result.exit_code == 0
    assert result.output.startswith("1 metadata key(s) written to")
    assert os.path.isfile(str(tmpdir.join("test.md")))
    assert tmpdir.join("test.md").read() == "Title: testing\n"
