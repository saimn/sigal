# -*- coding: utf-8 -*-

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

    if os.isatty(sys.stdout.fileno()) and not sys.platform.startswith('win'):
        formatter = ColoredFormatter()
    elif level == logging.DEBUG:
        formatter = Formatter('%(levelname)s - %(message)s')
    else:
        formatter = Formatter('%(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
