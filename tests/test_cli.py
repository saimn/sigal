# -*- coding: utf-8 -*-

import os
from click.testing import CliRunner

from sigal import init
from sigal import serve


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
