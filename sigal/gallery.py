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

from __future__ import absolute_import, print_function

import codecs
import locale
import logging
import markdown
import multiprocessing
import os
import sys
import zipfile

from os.path import join, normpath
from PIL import Image as PILImage
from pprint import pformat

from . import compat
from .image import process_image
from .log import colored, BLUE
from .utils import copy, check_or_create_dir
from .video import process_video
from .writer import Writer

DESCRIPTION_FILE = "index.md"


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
        self.ext_list = self.img_ext_list + self.vid_ext_list
        self.logger = logging.getLogger(__name__)

        # The dict containing all information
        self.db = {
            'paths_list': [],
            'skipped_dir': []
        }

        # basepath must to be a unicode string so that os.walk will return
        # unicode dirnames and filenames. If basepath is a str, we must
        # convert it to unicode.
        if compat.PY2 and isinstance(path, str):
            enc = locale.getpreferredencoding()
            self.basepath = path.decode(enc)
        else:
            self.basepath = path

        self.build()

    def get_subdirs(self, path):
        """Return the list of all sub-directories of path."""

        for name in self.db[path].get('subdir', []):
            subdir = normpath(join(path, name))
            yield subdir
            for subname in self.get_subdirs(subdir):
                yield subname

    def build(self):
        "Build the list of directories with images"

        if compat.PY2:
            sort_args = {'cmp': locale.strcoll}
        else:
            from functools import cmp_to_key
            sort_args = {'key': cmp_to_key(locale.strcoll)}

        # get information for each directory
        for path, dirnames, filenames in os.walk(self.basepath,
                                                 followlinks=True):
            relpath = os.path.relpath(path, self.basepath)

            # sort images and sub-albums by name
            filenames.sort(**sort_args)
            dirnames.sort(**sort_args)

            self.db['paths_list'].append(relpath)
            self.db[relpath] = {
                'medias': [f for f in filenames
                           if os.path.splitext(f)[1] in self.ext_list],
                'subdir': dirnames
            }
            self.db[relpath].update(get_metadata(path))

        path_media = (path for path in self.db['paths_list']
                      if self.db[path]['medias'] and path != '.')
        path_nomedia = (path for path in self.db['paths_list']
                        if not self.db[path]['medias'] and path != '.')

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
                parent = normpath(join(path, '..'))
                child = os.path.relpath(path, parent)
                self.db[parent]['subdir'].remove(child)

        self.logger.debug('Database:\n%s', pformat(self.db, width=120))

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


class Gallery(object):

    def __init__(self, settings, force=False, theme=None, ncpu=None):
        self.settings = settings
        self.force = force
        self.theme = theme
        self.logger = logging.getLogger(__name__)
        self.stats = {'image': 0, 'image_skipped': 0,
                      'video': 0, 'video_skipped': 0}

        try:
            cpu_count = multiprocessing.cpu_count()
        except NotImplementedError:
            cpu_count = 1

        if ncpu is None:
            ncpu = cpu_count
        else:
            try:
                ncpu = int(ncpu)
            except ValueError:
                self.logger.error('ncpu should be an integer value')
                ncpu = cpu_count

        if ncpu > 1:
            self.pool = multiprocessing.Pool(processes=ncpu)
        else:
            self.pool = None

        self.logger.info("Using %s cores", ncpu)

        paths = PathsDb(self.settings['source'], self.settings['img_ext_list'],
                        self.settings['vid_ext_list'])
        self.db = paths.db

    def build(self):
        "Create the image gallery"

        check_or_create_dir(self.settings['destination'])

        # loop on directories in reversed order, to process subdirectories
        # before their parent

        if self.pool:
            media_list = []

            for path in reversed(self.db['paths_list']):
                if len(self.db[path]['medias']) != 0:
                    for files in self.process_dir(path):
                        media_list.append(files)

            try:
                # map_async is needed to handle KeyboardInterrupt correctly
                self.pool.map_async(worker, media_list).get(9999)
                self.pool.close()
                self.pool.join()
            except KeyboardInterrupt:
                self.pool.terminate()
                sys.exit('Interrupted')

            print('')
        else:
            try:
                for path in reversed(self.db['paths_list']):
                    if len(self.db[path]['medias']) != 0:
                        for files in self.process_dir(path):
                            process_file(files)
                        print('')
            except KeyboardInterrupt:
                sys.exit('Interrupted')

        if self.settings['write_html']:
            self.writer = Writer(self.settings, self.settings['destination'],
                                 theme=self.theme)

            for path in reversed(self.db['paths_list']):
                self.writer.write(self.db, path)

    def process_dir(self, path):
        """Process a list of images in a directory."""

        media_files = [normpath(join(self.settings['source'], path, f))
                       for f in self.db[path]['medias']]

        # output dir for the current path
        outpath = normpath(join(self.settings['destination'], path))
        check_or_create_dir(outpath)

        # Create thumbnails directory and optionally the one for original img
        check_or_create_dir(join(outpath, self.settings['thumb_dir']))

        if self.settings['keep_orig']:
            check_or_create_dir(join(outpath, self.settings['orig_dir']))

        if sys.stdout.isatty():
            print(colored('->', BLUE),
                  u"{} : {} files".format(path, len(media_files)))
        else:
            self.logger.warn("%s : %d files", path, len(media_files))

        # loop on images
        if self.settings['zip_gallery']:
            zip_files(join(outpath, self.settings['zip_gallery']), media_files)

        for f in media_files:
            filename = os.path.split(f)[1]
            base, ext = os.path.splitext(filename)

            if ext in self.settings['img_ext_list']:
                outname = join(outpath, filename)
                filetype = 'image'
            elif ext in self.settings['vid_ext_list']:
                outname = join(outpath, base + '.webm')
                filetype = 'video'
            else:
                raise FileExtensionError

            if os.path.isfile(outname) and not self.force:
                self.logger.info("%s exists - skipping", filename)
                self.stats[filetype + '_skipped'] += 1
            else:
                if self.settings['keep_orig']:
                    copy(f, join(outpath, self.settings['orig_dir'], filename),
                         symlink=self.settings['orig_link'])

                self.stats[filetype] += 1
                yield filetype, f, outpath, self.settings


def process_file(args):
    logger = logging.getLogger(__name__)
    logger.info('Processing %s', args[1])

    if logger.getEffectiveLevel() > 20:
        print('.', end='')
        sys.stdout.flush()

    if args[0] == 'image':
        return process_image(*args[1:])
    elif args[0] == 'video':
        return process_video(*args[1:])


def worker(args):
    try:
        process_file(args)
    except KeyboardInterrupt:
        return 'KeyboardException'


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


def zip_files(archive_path, filepaths):
    archive = zipfile.ZipFile(archive_path, 'w')

    for p in filepaths:
        filename = os.path.split(p)[1]
        archive.write(p, filename)

    archive.close()
