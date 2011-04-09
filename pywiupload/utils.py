#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# pywiUpload - Piwigo gallery generator
# Copyright (C) 2009-2011 Simon - saimon.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; If not, see http://www.gnu.org/licenses/

"""Various stuff.

- Fonctions used to manage files (get_filelist).
"""

import os

def get_filelist(directory, extensions):
    "get list of files of particular extensions"
    filelist = [os.path.normcase(f) for f in os.listdir(directory)]
    return [os.path.join(directory, f) for f in filelist \
            if os.path.splitext(f)[1] in extensions]

