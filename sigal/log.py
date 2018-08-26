# Copyright (c) 2013-2018 - Simon Conseil

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import logging
import os
import sys

from logging import Formatter

# The background is set with 40 plus the number of the color, and the
# foreground with 30
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = [30 + i
                                                         for i in range(8)]

COLORS = {
    'DEBUG': BLUE,
    'INFO': GREEN,
    'WARNING': YELLOW,
    'ERROR': RED,
    'CRITICAL': MAGENTA,
}

# These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;{0}m{1}{2}"
BOLD_SEQ = "\033[1m"


def colored(text, color):
    return COLOR_SEQ.format(color, text, RESET_SEQ)


class ColoredFormatter(Formatter):

    def format(self, record):
        level = record.levelname
        return colored(level, COLORS[level]) + ': ' + record.getMessage()


def init_logging(name, level=logging.INFO):
    """Logging config

    Set the level and create a more detailed formatter for debug mode.

    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    try:
        if os.isatty(sys.stdout.fileno()) and \
                not sys.platform.startswith('win'):
            formatter = ColoredFormatter()
        elif level == logging.DEBUG:
            formatter = Formatter('%(levelname)s - %(message)s')
        else:
            formatter = Formatter('%(message)s')
    except Exception:
        # This fails when running tests with click (test_build)
        formatter = Formatter('%(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
