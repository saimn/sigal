# -*- coding:utf-8 -*-

# Copyright (c) 2009-2013 - Simon Conseil
# Copyright (c) 2013      - Christophe-Marie Duquesne

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

from __future__ import absolute_import

import codecs
import locale
import logging
import markdown
import os
import shutil
import sys
import zipfile

from clint.textui import progress, colored
from os.path import join
from PIL import Image as PILImage

import sigal.image
import sigal.video
from .settings import get_thumb
from .writer import Writer

DESCRIPTION_FILE = "index.md"

# Label with for the progress bar. The max value is 48 character = 80 - 32 for
# the progress bar.
MAX_LABEL_WIDTH = 45


class FileExtensionError(Exception):
    """Raised if we made an error when handling file extensions"""
    pass


class PathsDb(object):
    """Container for all the information on the directory structure.

    All the info is stored in a dictionnary, `self.db`. This class also has
    methods to build this dictionnary.

    """

    def __init__(self, path, img_ext_list, vid_ext_list):
        self.img_ext_list = img_ext_list
        self.vid_ext_list = vid_ext_list
        self.logger = logging.getLogger(__name__)

        # basepath must to be a unicode string so that os.walk will return
        # unicode dirnames and filenames. If basepath is a str, we must
        # convert it to unicode.
        if isinstance(path, str):
            enc = locale.getpreferredencoding()
            self.basepath = path.decode(enc)
        else:
            self.basepath = path

    def get_subdirs(self, path):
        """Return the list of all sub-directories of path."""

        subdir = [os.path.normpath(os.path.join(path, sub))
                  for sub in self.db[path].get('subdir', [])]
        if subdir:
            return subdir + reduce(lambda x, y: x + y,
                                   map(self.get_subdirs, subdir))
        else:
            return []

    def build(self):
        "Build the list of directories with images"

        # The dict containing all information
        self.db = {
            'paths_list': [],
            'skipped_dir': []
        }

        # get information for each directory
        for path, dirnames, filenames in os.walk(self.basepath):
            relpath = os.path.relpath(path, self.basepath)

            # sort images and sub-albums by name
            filenames.sort(cmp=locale.strcoll)
            dirnames.sort(cmp=locale.strcoll)

            self.db['paths_list'].append(relpath)
            self.db[relpath] = {
                'medias': [f for f in filenames if os.path.splitext(f)[1]
                           in (self.img_ext_list + self.vid_ext_list)],
                'subdir': dirnames
            }
            self.db[relpath].update(get_metadata(path))

        path_media = [path for path in self.db['paths_list']
                      if self.db[path]['medias'] and path != '.']
        path_nomedia = [path for path in self.db['paths_list']
                        if not self.db[path]['medias'] and path != '.']

        # dir with images: check the thumbnail, and find it if necessary
        for path in path_media:
            self.check_thumbnail(path)

        # dir without images, start with the deepest ones
        for path in reversed(sorted(path_nomedia, key=lambda x: x.count('/'))):
            for subdir in self.get_subdirs(path):
                # use the thumbnail of their sub-directories
                if self.db[subdir].get('thumbnail', ''):
                    self.db[path]['thumbnail'] = join(
                        os.path.relpath(subdir, path),
                        self.db[subdir]['thumbnail'])
                    break

            if not self.db[path].get('thumbnail', ''):
                # else remove all info about this directory
                self.logger.info("Directory '%s' is empty", path)
                self.db['skipped_dir'].append(path)
                self.db['paths_list'].remove(path)
                del self.db[path]
                parent = os.path.normpath(join(path, '..'))
                child = os.path.relpath(path, parent)
                self.db[parent]['subdir'].remove(child)

    def check_thumbnail(self, path):
        "Find the thumbnail image for a given path."

        # stop if it is already set and a valid file
        alb_thumb = self.db[path].setdefault('thumbnail', '')
        if alb_thumb and os.path.isfile(join(self.basepath, path, alb_thumb)):
            return

        # find and return the first landscape image
        for f in self.db[path]['medias']:
            base, ext = os.path.splitext(f)
            if ext in self.img_ext_list:
                im = PILImage.open(join(self.basepath, path, f))
                if im.size[0] > im.size[1]:
                    self.db[path]['thumbnail'] = f
                    return

        # else simply return the 1st media file
        if self.db[path]['medias']:
            self.db[path]['thumbnail'] = self.db[path]['medias'][0]
            return

        self.db[path]['thumbnail'] = ''


class Gallery(object):
    "Prepare images"

    def __init__(self, settings, force=False, theme=None):
        self.settings = settings
        self.force = force
        self.logger = logging.getLogger(__name__)

        if self.settings['write_html']:
            self.writer = Writer(settings, self.settings['destination'],
                                 theme=theme)

        self.paths = PathsDb(self.settings['source'],
                             self.settings['img_ext_list'],
                             self.settings['vid_ext_list'])
        self.paths.build()
        self.db = self.paths.db

    def build(self):
        "Create the image gallery"

        check_or_create_dir(self.settings['destination'])

        # Compute the label with for the progress bar
        label_width = max((len(p) for p in self.db['paths_list'])) + 1
        label_width = min(label_width, MAX_LABEL_WIDTH)

        # loop on directories in reversed order, to process subdirectories
        # before their parent
        for path in reversed(self.db['paths_list']):
            source = self.settings['source']
            media_files = [os.path.normpath(join(source, path, f))
                           for f in self.db[path]['medias']]

            # output dir for the current path
            outpath = os.path.normpath(join(self.settings['destination'],
                                            path))
            check_or_create_dir(outpath)

            if len(media_files) != 0:
                self.process_dir(media_files, outpath, path,
                                 label_width=label_width)

            if self.settings['write_html']:
                self.writer.write(self.db, path)

    def process_dir(self, media_files, outpath, dirname, label_width=20):
        """Process a list of images in a directory."""

        # Create thumbnails directory and optionally the one for original img
        check_or_create_dir(join(outpath, self.settings['thumb_dir']))

        if self.settings['keep_orig']:
            check_or_create_dir(join(outpath, self.settings['orig_dir']))

        # use progressbar if level is > INFO
        if self.logger.getEffectiveLevel() > 20:
            label = dirname[:MAX_LABEL_WIDTH - 1]
            label = colored.green(label.ljust(label_width))
            media_iterator = progress.bar(media_files, label=label)
        else:
            media_iterator = iter(media_files)
            self.logger.info("")
            self.logger.info(":: Processing '%s' [%i img/vid]",
                             colored.green(dirname), len(media_files))
            self.logger.info("")

        try:
            # loop on images
            if self.settings['zip_gallery']:
                self._zip_files(outpath, media_files)

            for f in media_iterator:
                filename = os.path.split(f)[1]
                base, ext = os.path.splitext(filename)
                if ext in self.settings['img_ext_list']:
                    outname = join(outpath, filename)
                elif ext in self.settings['vid_ext_list']:
                    outname = join(outpath, base + '.webm')
                else:
                    raise FileExtensionError

                if os.path.isfile(outname) and not self.force:
                    self.logger.info("%s exists - skipping", filename)
                else:
                    self.logger.info(filename)
                    if ext in self.settings['img_ext_list']:
                        process_image(f, outpath, self.settings)
                    elif ext in self.settings['vid_ext_list']:
                        process_video(f, outpath, self.settings)
                    else:
                        raise FileExtensionError

        except KeyboardInterrupt:
            sys.exit('Interrupted')

    def _zip_files(self, outpath, filepaths):
        archive_name = join(outpath, str(self.settings['zip_gallery']))
        archive = zipfile.ZipFile(archive_name, 'w')

        for p in filepaths:
            filename = os.path.split(p)[1]
            archive.write(p, filename)

        archive.close()


def process_image(filepath, outpath, settings):
    """Process one image: resize, create thumbnail."""

    filename = os.path.split(filepath)[1]
    outname = join(outpath, filename)
    ext = os.path.splitext(filename)

    if ext in ['.jpg', '.jpeg', '.JPG', '.JPEG']:
        options = settings['jpg_options']
    elif ext == '.png':
        options = {'optimize': True}
    else:
        options = {}

    if settings['keep_orig']:
        shutil.copy(filepath, join(outpath, settings['orig_dir'], filename))

    sigal.image.generate_image(filepath, outname, settings, options=options)

    if settings['make_thumbs']:
        thumb_name = join(outpath, get_thumb(settings, filename))
        sigal.image.generate_thumbnail(
            outname, thumb_name, settings['thumb_size'],
            fit=settings['thumb_fit'], options=options)


def process_video(filepath, outpath, settings):
    """Process one image: resize, create thumbnail."""

    filename = os.path.split(filepath)[1]
    base, ext = os.path.splitext(filename)
    outname = join(outpath, base + '.webm')

    if settings['keep_orig']:
        shutil.copy(filepath, join(outpath, settings['orig_dir'], filename))

    # TODO: Add specific video size settings
    sigal.video.generate_video(filepath, outname, settings['img_size'],
                               settings['webm_options'])

    if settings['make_thumbs']:
        thumb_name = join(outpath, get_thumb(settings, filename))
        sigal.video.generate_thumbnail(
            outname, thumb_name, settings['thumb_size'],
            fit=settings['thumb_fit'], options=settings['jpg_options'])


def get_metadata(path):
    """ Get album metadata from DESCRIPTION_FILE:

    - title
    - thumbnail image
    - description

    """
    descfile = join(path, DESCRIPTION_FILE)

    if not os.path.isfile(descfile):
        # default: get title from directory name
        meta = {
            'title': os.path.basename(path).replace('_', ' ')
            .replace('-', ' ').capitalize(),
            'description': '',
            'thumbnail': '',
            'meta': {}
        }
    else:
        with codecs.open(descfile, "r", "utf-8") as f:
            text = f.read()

        md = markdown.Markdown(extensions=['meta'])
        html = md.convert(text)

        meta = {
            'title': md.Meta.get('title', [''])[0],
            'description': html,
            'thumbnail': md.Meta.get('thumbnail', [''])[0],
            'meta': md.Meta.copy()
        }

    return meta


def check_or_create_dir(path):
    "Create the directory if it does not exist"

    if not os.path.isdir(path):
        os.makedirs(path)
