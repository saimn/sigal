# -*- coding:utf-8 -*-

# Copyright (c) 2009-2014 - Simon Conseil
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

import fnmatch
import logging
import multiprocessing
import os
import sys
import zipfile

from collections import defaultdict
from datetime import datetime
from functools import partial
from os.path import isfile, join, splitext
from PIL import Image as PILImage

from . import image, video, signals
from .compat import UnicodeMixin, strxfrm, url_quote
from .image import process_image, get_exif_tags
from .log import colored, BLUE
from .settings import get_thumb
from .utils import copy, check_or_create_dir, url_from_path, read_markdown
from .video import process_video
from .writer import Writer


class Media(UnicodeMixin):
    """Base Class for media files.

    Attributes:

    - ``type``: ``"image"`` or ``"video"``.
    - ``filename``: Filename of the resized image.
    - ``thumbnail``: Location of the corresponding thumbnail image.
    - ``big``: If not None, location of the unmodified image.
    - ``exif``: If not None contains a dict with the most common tags. For more
        information, see :ref:`simple-exif-data`.
    - ``raw_exif``: If not ``None``, it contains the raw EXIF tags.

    """

    type = ''
    extensions = ()

    def __init__(self, filename, path, settings):
        self.src_filename = self.filename = self.url = filename
        self.path = path
        self.settings = settings

        self.src_path = join(settings['source'], path, filename)
        self.dst_path = join(settings['destination'], path, filename)

        self.thumb_name = get_thumb(self.settings, self.filename)
        self.thumb_path = join(settings['destination'], path, self.thumb_name)

        self.logger = logging.getLogger(__name__)
        self.raw_exif = None
        self.exif = None
        self.date = None
        self._get_metadata()
        signals.media_initialized.send(self)

    def __repr__(self):
        return "<%s>(%r)" % (self.__class__.__name__, str(self))

    def __unicode__(self):
        return join(self.path, self.filename)

    @property
    def big(self):
        """Path to the original image, if ``keep_orig`` is set (relative to the
        album directory).
        """
        if self.settings['keep_orig']:
            return os.path.join(self.settings['orig_dir'], self.src_filename)
        else:
            return None

    @property
    def thumbnail(self):
        """Path to the thumbnail image (relative to the album directory)."""

        if not os.path.isfile(self.thumb_path):
            # if thumbnail is missing (if settings['make_thumbs'] is False)
            if self.type == 'image':
                generator = image.generate_thumbnail
            elif self.type == 'video':
                generator = video.generate_thumbnail

            self.logger.debug('Generating thumbnail for %r', self)
            try:
                generator(self.src_path, self.thumb_path,
                          self.settings['thumb_size'],
                          fit=self.settings['thumb_fit'])
            except Exception as e:
                self.logger.error('Failed to generate thumbnail: %s', e)
                return
        return url_from_path(self.thumb_name)

    def _get_metadata(self):
        """ Get image metadata from filename.md: title, description, meta."""
        self.description = ''
        self.meta = {}
        self.title = ''

        descfile = splitext(self.src_path)[0] + '.md'
        if isfile(descfile):
            meta = read_markdown(descfile)
            for key, val in meta.items():
                setattr(self, key, val)


class Image(Media):
    """Gather all informations on an image file."""

    type = 'image'
    extensions = ('.jpg', '.jpeg', '.png')

    def __init__(self, filename, path, settings):
        super(Image, self).__init__(filename, path, settings)
        self.raw_exif, self.exif = get_exif_tags(self.src_path)
        if self.exif is not None and 'dateobj' in self.exif:
            self.date = self.exif['dateobj']


class Video(Media):
    """Gather all informations on a video file."""

    type = 'video'
    extensions = ('.mov', '.avi', '.mp4', '.webm', '.ogv')

    def __init__(self, filename, path, settings):
        super(Video, self).__init__(filename, path, settings)
        base = splitext(filename)[0]
        self.src_filename = filename
        self.filename = self.url = base + '.webm'
        self.dst_path = join(settings['destination'], path, base + '.webm')


class Album(UnicodeMixin):
    """Gather all informations on an album.

    Attributes:

    :var description_file: Name of the Markdown file which gives information
        on an album
    :ivar index_url: URL to the index page.
    :ivar output_file: Name of the output HTML file
    :ivar meta: Meta data from the Markdown file.
    :ivar description: description from the Markdown file.

    For details how to annotate your albums with meta data, see
    :doc:`album_information`.

    """

    description_file = "index.md"
    output_file = 'index.html'

    def __init__(self, path, settings, dirnames, filenames, gallery):
        self.path = path
        self.name = path.split(os.path.sep)[-1]
        self.gallery = gallery
        self.settings = settings
        self.orig_path = None
        self._thumbnail = None

        if path == '.':
            self.src_path = settings['source']
            self.dst_path = settings['destination']
        else:
            self.src_path = join(settings['source'], path)
            self.dst_path = join(settings['destination'], path)

        self.logger = logging.getLogger(__name__)
        self._get_metadata()

        # optionally add index.html to the URLs
        self.url_ext = self.output_file if settings['index_in_url'] else ''

        self.index_url = url_from_path(os.path.relpath(
            settings['destination'], self.dst_path)) + '/' + self.url_ext

        # sort sub-albums
        dirnames.sort(key=strxfrm, reverse=settings['albums_sort_reverse'])
        self.subdirs = dirnames

        #: List of all medias in the album (:class:`~sigal.gallery.Image` and
        #: :class:`~sigal.gallery.Video`).
        self.medias = medias = []
        self.medias_count = defaultdict(int)

        for f in filenames:
            ext = splitext(f)[1]
            if ext.lower() in Image.extensions:
                media = Image(f, self.path, settings)
            elif ext.lower() in Video.extensions:
                media = Video(f, self.path, settings)
            else:
                continue

            self.medias_count[media.type] += 1
            medias.append(media)

        # sort images
        if medias:
            medias_sort_attr = settings['medias_sort_attr']
            if medias_sort_attr == 'date':
                key = lambda s: s.date or datetime.now()
            else:
                key = lambda s: strxfrm(getattr(s, medias_sort_attr))

            medias.sort(key=key, reverse=settings['medias_sort_reverse'])

        signals.album_initialized.send(self)

    def __repr__(self):
        return "<%s>(path=%r, title=%r)" % (self.__class__.__name__, self.path,
                                            self.title)

    def __unicode__(self):
        return (u"{} : ".format(self.path) +
                ', '.join("{} {}s".format(count, _type)
                          for _type, count in self.medias_count.items()))

    def __len__(self):
        return len(self.medias)

    def __iter__(self):
        return iter(self.medias)

    def _get_metadata(self):
        """Get album metadata from `description_file` (`index.md`):

        -> title, thumbnail image, description

        """
        descfile = join(self.src_path, self.description_file)
        self.description = ''
        self.meta = {}
        # default: get title from directory name
        self.title = os.path.basename(self.path if self.path != '.'
                                      else self.src_path)

        if isfile(descfile):
            meta = read_markdown(descfile)
            for key, val in meta.items():
                setattr(self, key, val)

    def create_output_directories(self):
        """Create output directories for thumbnails and original images."""
        check_or_create_dir(self.dst_path)

        if self.medias:
            check_or_create_dir(join(self.dst_path,
                                     self.settings['thumb_dir']))

        if self.medias and self.settings['keep_orig']:
            self.orig_path = join(self.dst_path, self.settings['orig_dir'])
            check_or_create_dir(self.orig_path)

    @property
    def images(self):
        """List of images (:class:`~sigal.gallery.Image`)."""
        for media in self.medias:
            if media.type == 'image':
                yield media

    @property
    def videos(self):
        """List of videos (:class:`~sigal.gallery.Video`)."""
        for media in self.medias:
            if media.type == 'video':
                yield media

    @property
    def albums(self):
        """List of :class:`~sigal.gallery.Album` objects for each
        sub-directory.
        """
        root_path = self.path if self.path != '.' else ''
        return [self.gallery.albums[join(root_path, path)]
                for path in self.subdirs]

    @property
    def url(self):
        """URL of the album, relative to its parent."""
        url = self.name.encode('utf-8')
        return url_quote(url) + '/' + self.url_ext

    @property
    def thumbnail(self):
        """Path to the thumbnail of the album."""

        if self._thumbnail:
            # stop if it is already set
            return url_from_path(self._thumbnail)

        # Test the thumbnail from the Markdown file.
        thumbnail = self.meta.get('thumbnail', [''])[0]

        if thumbnail and isfile(join(self.src_path, thumbnail)):
            self._thumbnail = join(self.name, get_thumb(self.settings,
                                                        thumbnail))
            self.logger.debug("Thumbnail for %r : %s", self, self._thumbnail)
            return url_from_path(self._thumbnail)
        else:
            # find and return the first landscape image
            for f in self.medias:
                ext = splitext(f.filename)[1]
                if ext.lower() in Image.extensions:
                    try:
                        im = PILImage.open(f.src_path)
                    except:
                        self.logger.error("Failed to open %s", f.src_path)
                    else:
                        if im.size[0] > im.size[1]:
                            self._thumbnail = join(self.name, f.thumbnail)
                            self.logger.debug(
                                "Use 1st landscape image as thumbnail for %r :"
                                " %s", self, self._thumbnail)
                            return url_from_path(self._thumbnail)

            # else simply return the 1st media file
            if not self._thumbnail and self.medias:
                self._thumbnail = join(self.name, self.medias[0].thumbnail)
                self.logger.debug("Use the 1st image as thumbnail for %r : %s",
                                  self, self._thumbnail)
                return url_from_path(self._thumbnail)

            # use the thumbnail of their sub-directories
            if not self._thumbnail:
                for path, album in self.gallery.get_albums(self.path):
                    if album.thumbnail:
                        self._thumbnail = join(self.name, album.thumbnail)
                        self.logger.debug(
                            "Using thumbnail from sub-directory for %r : %s",
                            self, self._thumbnail)
                        return url_from_path(self._thumbnail)

        self.logger.error('Thumbnail not found for %r', self)
        return None

    @property
    def breadcrumb(self):
        """List of ``(url, title)`` tuples defining the current breadcrumb
        path.
        """
        if self.path == '.':
            return []

        path = self.path
        breadcrumb = [((self.url_ext or '.'), self.title)]

        while True:
            path = os.path.normpath(os.path.join(path, '..'))
            if path == '.':
                break

            url = (url_from_path(os.path.relpath(path, self.path)) + '/' +
                   self.url_ext)
            breadcrumb.append((url, self.gallery.albums[path].title))

        breadcrumb.reverse()
        return breadcrumb

    @property
    def zip(self):
        """Make a ZIP archive with all media files and return its path.

        If the ``zip_gallery`` setting is set,it contains the location of a zip
        archive with all original images of the corresponding directory.

        """
        zip_gallery = self.settings['zip_gallery']

        if zip_gallery and len(self) > 0:
            archive_path = join(self.dst_path, zip_gallery)
            archive = zipfile.ZipFile(archive_path, 'w')

            if self.settings['zip_media_format'] == 'orig':
                for p in self:
                    archive.write(p.src_path, os.path.split(p.src_path)[1])
            else:
                for p in self:
                    archive.write(p.dst_path, os.path.split(p.dst_path)[1])

            archive.close()
            self.logger.debug('Created ZIP archive %s', archive_path)
            return zip_gallery
        else:
            return None


class Gallery(object):

    def __init__(self, settings, ncpu=None):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.stats = {'image': 0, 'image_skipped': 0,
                      'video': 0, 'video_skipped': 0}
        self.init_pool(ncpu)
        check_or_create_dir(settings['destination'])

        # Build the list of directories with images
        albums = self.albums = {}
        src_path = self.settings['source']

        ignore_dirs = settings['ignore_directories']
        ignore_files = settings['ignore_files']

        for path, dirs, files in os.walk(src_path, followlinks=True,
                                         topdown=False):
            relpath = os.path.relpath(path, src_path)

            # Test if the directory match the ignore_dirs settings
            if ignore_dirs and any(fnmatch.fnmatch(relpath, ignore)
                                   for ignore in ignore_dirs):
                self.logger.info('Ignoring %s', relpath)
                continue

            # Remove files that match the ignore_files settings
            if ignore_files:
                files_path = {join(relpath, f) for f in files}
                for ignore in ignore_files:
                    files_path -= set(fnmatch.filter(files_path, ignore))

                self.logger.debug('Files before filtering: %r', files)
                files = [os.path.split(f)[1] for f in files_path]
                self.logger.debug('Files after filtering: %r', files)

            # Remove sub-directories that have been ignored in a previous
            # iteration (as topdown=False, sub-directories are processed before
            # their parent
            for d in dirs[:]:
                path = join(relpath, d) if relpath != '.' else d
                if path not in albums.keys():
                    dirs.remove(d)

            album = Album(relpath, settings, dirs, files, self)

            if not album.medias and not album.albums:
                self.logger.info('Skip empty album: %r', album)
            else:
                album.create_output_directories()
                albums[relpath] = album

        self.logger.debug('Albums:\n%r', albums.values())
        signals.gallery_initialized.send(self)

    @property
    def title(self):
        """Title of the gallery."""
        return self.settings['title'] or self.albums['.'].title

    def init_pool(self, ncpu):
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

        self.logger.info("Using %s cores", ncpu)
        if ncpu > 1:
            self.pool = multiprocessing.Pool(processes=ncpu)
        else:
            self.pool = None

    def get_albums(self, path):
        """Return the list of all sub-directories of path."""

        for name in self.albums[path].subdirs:
            subdir = os.path.normpath(join(path, name))
            yield subdir, self.albums[subdir]
            for subname, album in self.get_albums(subdir):
                yield subname, self.albums[subdir]

    def build(self, force=False):
        "Create the image gallery"

        if not self.albums:
            self.logger.warning("No albums found.")
            return

        log_func = (partial(print, colored('->', BLUE)) if sys.stdout.isatty()
                    else self.logger.warn)

        # loop on directories in reversed order, to process subdirectories
        # before their parent
        media_list = []
        processor = media_list.append if self.pool else process_file

        try:
            for album in self.albums.values():
                if len(album) > 0:
                    log_func(str(album))
                    for files in self.process_dir(album, force=force):
                        processor(files)
                else:
                    self.logger.info('Album %r is empty', album)
        except KeyboardInterrupt:
            sys.exit('Interrupted')

        if self.pool:
            try:
                # map_async is needed to handle KeyboardInterrupt correctly
                self.pool.map_async(worker, media_list).get(9999)
                self.pool.close()
                self.pool.join()
            except KeyboardInterrupt:
                self.pool.terminate()
                sys.exit('Interrupted')

            print('')

        if self.settings['write_html']:
            writer = Writer(self.settings, index_title=self.title)
            for album in self.albums.values():
                writer.write(album)

        signals.gallery_build.send(self)

    def process_dir(self, album, force=False):
        """Process a list of images in a directory."""

        for f in album:
            if isfile(f.dst_path) and not force:
                self.logger.info("%s exists - skipping", f.filename)
                self.stats[f.type + '_skipped'] += 1
            else:
                if self.settings['keep_orig']:
                    copy(f.src_path, join(album.orig_path, f.filename),
                         symlink=self.settings['orig_link'])

                self.stats[f.type] += 1
                yield f.type, f.src_path, album.dst_path, self.settings


def process_file(args):
    ftype, src_path, dst_path, settings = args
    logger = logging.getLogger(__name__)
    logger.info('Processing %s', src_path)

    if logger.getEffectiveLevel() > 20:
        print('.', end='')
        sys.stdout.flush()

    if ftype == 'image':
        return process_image(src_path, dst_path, settings)
    elif ftype == 'video':
        return process_video(src_path, dst_path, settings)


def worker(args):
    try:
        process_file(args)
    except KeyboardInterrupt:
        return 'KeyboardException'
