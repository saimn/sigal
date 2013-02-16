# -*- coding:utf-8 -*-

# Copyright (c) 2009-2013 - Simon Conseil

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
import logging
import markdown
import os
import PIL

from clint.textui import progress, colored
from os.path import join

from .image import Image, copy_exif
from .settings import get_thumb
from .writer import Writer

DESCRIPTION_FILE = "index.md"


class PathsDb(object):
    def __init__(self, path, ext_list):
        self.basepath = path
        self.ext_list = ext_list
        self.logger = logging.getLogger(__name__)

        # The dict containing all information
        self.db = {
            'paths_list': [],
            'skipped_dir': []
        }

    def build(self):
        "Build the list of directories with images"

        for path, dirnames, filenames in os.walk(self.basepath):
            relpath = os.path.relpath(path, self.basepath)

            # sort images and sub-albums by name
            filenames.sort(key=str.lower)
            dirnames.sort(key=str.lower)

            images = [f for f in filenames
                      if os.path.splitext(f)[1] in self.ext_list]

            # skip this directory if it doesn't contain images
            if relpath != '.' and not images:
                self.db['skipped_dir'].append(relpath)
                self.logger.info("Directory '%s' is empty", relpath)
                continue

            self.db['paths_list'].append(relpath)
            self.db[relpath] = {'img': images, 'subdir': dirnames}
            self.db[relpath].update(get_metadata(path))

            if relpath != '.':
                alb_thumb = self.db[relpath].setdefault('representative', '')
                if (not alb_thumb) or \
                   (not os.path.isfile(join(path, alb_thumb))):
                    alb_thumb = self.find_representative(relpath)
                    self.db[relpath]['representative'] = alb_thumb

        # cleanup: remove skipped directories
        for path in self.db['paths_list']:
            subdir = iter(self.db[path]['subdir'])
            self.db[path]['subdir'] = [
                d for d in subdir if d not in self.db['skipped_dir']]

    def find_representative(self, path):
        "Find the representative image for a given path"

        for f in self.db[path]['img']:
            # find and return the first landscape image
            im = PIL.Image.open(join(self.basepath, path, f))
            if im.size[0] > im.size[1]:
                return f

        # else simply return the 1st image
        return self.db[path]['img'][0]


class Gallery(object):
    "Prepare images"

    def __init__(self, settings, input_dir, output_dir, force=False,
                 theme=None):
        self.settings = settings
        self.force = force
        self.input_dir = os.path.abspath(input_dir)
        self.output_dir = os.path.abspath(output_dir)
        self.logger = logging.getLogger(__name__)
        self.writer = Writer(settings, output_dir, theme=theme)

        self.paths = PathsDb(self.input_dir, self.settings['ext_list'])
        self.paths.build()
        self.db = self.paths.db

    def build(self):
        "Create the image gallery"

        self.logger.info("Generate gallery in %s ...", self.output_dir)
        check_or_create_dir(self.output_dir)

        # Compute the label with for the progress bar. The max value is 48
        # character = 80 - 32 for the progress bar.
        label_width = max((len(p) for p in self.db['paths_list'])) + 1
        label_width = min(label_width, 48)

        # loop on directories in reversed order, to process subdirectories
        # before their parent
        for path in reversed(self.db['paths_list']):
            imglist = [join(self.input_dir, path, f)
                       for f in self.db[path]['img']]

            # output dir for the current path
            img_out = join(self.output_dir, path)
            check_or_create_dir(img_out)

            if len(imglist) != 0:
                self.process_dir(imglist, img_out, path,
                                 label_width=label_width)

            self.writer.write(self.db, path)

    def process_image(self, filepath, outpath):
        """Process one image: resize, create thumbnail, copy exif."""

        filename = os.path.split(filepath)[1]
        outname = join(outpath, filename)

        self.logger.info(filename)
        img = Image(filepath)

        if self.settings['keep_orig']:
            img.save(join(outpath, self.settings['orig_dir'], filename),
                     **self.settings['jpg_options'])

        img.resize(self.settings['img_size'])

        if self.settings['copyright']:
            img.add_copyright(self.settings['copyright'])

        img.save(outname, **self.settings['jpg_options'])

        if self.settings['make_thumbs']:
            thumb_name = join(outpath, get_thumb(self.settings, filename))
            img.thumbnail(thumb_name, self.settings['thumb_size'],
                          fit=self.settings['thumb_fit'],
                          quality=self.settings['jpg_options']['quality'])

        if self.settings['copy_exif']:
            copy_exif(filepath, outname)

    def process_dir(self, imglist, outpath, dirname, label_width=20):
        """Process a list of images in a directory."""

        # Create thumbnails directory and optionally the one for original img
        check_or_create_dir(join(outpath, self.settings['thumb_dir']))

        if self.settings['keep_orig']:
            check_or_create_dir(join(outpath, self.settings['orig_dir']))

        # use progressbar if level is > INFO
        if self.logger.getEffectiveLevel() > 20:
            label = colored.green(dirname.ljust(label_width))
            img_iterator = progress.bar(imglist, label=label)
        else:
            img_iterator = iter(imglist)
            self.logger.info(":: Processing '%s' [%i images]",
                             colored.green(dirname), len(imglist))

        # loop on images
        for f in img_iterator:
            filename = os.path.split(f)[1]
            outname = join(outpath, filename)

            if os.path.isfile(outname) and not self.force:
                self.logger.info("%s exists - skipping", filename)
            else:
                self.process_image(f, outpath)


def get_metadata(path):
    """ Get album metadata from DESCRIPTION_FILE:

    - title
    - representative image
    - description
    """

    descfile = join(path, DESCRIPTION_FILE)
    meta = {}

    if not os.path.isfile(descfile):
        # default: get title from directory name
        meta['title'] = os.path.basename(path).replace('_', ' ').\
            replace('-', ' ').capitalize()
    else:
        md = markdown.Markdown(extensions=['meta'])

        with codecs.open(descfile, "r", "utf-8") as f:
            text = f.read()

        html = md.convert(text)

        meta = {
            'title': md.Meta.get('title', [''])[0],
            'description': html,
            'representative': md.Meta.get('representative', [''])[0]
        }

    return meta


def check_or_create_dir(path):
    "Create the directory if it does not exist"

    if not os.path.isdir(path):
        os.makedirs(path)
