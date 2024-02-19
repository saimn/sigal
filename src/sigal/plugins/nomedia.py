# Copyright 2017 - Tilman 't.animal' Adler

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

""" This plugin offers more fine-grained control over exluded images and
folders, similarly to how it's handled on Android.

To ignore a folder or image put a ``.nomedia`` file next to it in its parent
folder and put its name into the file.  E.g.::

    content of folder:
        IMG_3425.JPG, IMG_2426.JPG, IMG_2427.JPG, subfolder, .nomedia
    content of .nomedia:
        IMG_2426.JPG
        IMG_2427.JPG
        subfolder

will ignore all images but IMG_3425.JPG and the subfolder.

Alternatively, if you put a ``.nomedia`` file into a folder and leave it blank
(i.e. an empty file called ``.nomedia`` in a folder containing images), this
ignores the whole folder it's located in (like on Android).

WARNING: When you have a pre-existing gallery from a previous run of sigal
adding a new ``.nomedia`` file will not remove the newly ignored images/albums
from the existing gallery (only the entries in the parent gallery pointing to
it).  They might still be reachable thereafter. Either remove the whole gallery
to be sure or remove the ignored files/folders inside the gallery to remove
them for good.

"""

import logging
import os

from sigal import signals

logger = logging.getLogger(__name__)


def filter_nomedia(album, settings=None):
    """Removes all filtered Media and subdirs from an Album"""
    nomediapath = os.path.join(album.src_path, ".nomedia")

    if not os.path.isfile(nomediapath):
        return

    if os.path.getsize(nomediapath) == 0:
        logger.info(
            "Ignoring album '%s' because of present 0-byte .nomedia file", album.name
        )
        album.subdirs.clear()
        album.medias.clear()

    else:
        with open(nomediapath) as nomediaFile:
            logger.info("Found a .nomedia file in %s, ignoring its entries", album.name)
            ignored = nomediaFile.read().split("\n")

            for media in album.medias[:]:
                if media.src_filename in ignored:
                    album.medias.remove(media)
            for dirname in album.subdirs[:]:
                if dirname in ignored:
                    album.subdirs.remove(dirname)


def register(settings):
    signals.album_initialized.connect(filter_nomedia)
