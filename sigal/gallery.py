# -*- coding:utf-8 -*-

# Copyright (c) 2009-2014 - Simon Conseil
# Copyright (c) 2013      - Christophe-Marie Duquesne
# Copyright (c) 2014      - Jonas Kaufmann

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
import pickle
import sys
import zipfile

from click import progressbar, get_terminal_size
from collections import defaultdict
from datetime import datetime
from itertools import cycle
from os.path import isfile, join, splitext
from PIL import Image as PILImage

from . import image, video, signals
from .compat import PY2, UnicodeMixin, strxfrm, url_quote, text_type
from .image import process_image, get_exif_tags, get_exif_data
from .settings import get_thumb
from .utils import (Devnull, copy, check_or_create_dir, url_from_path,
                    read_markdown, cached_property)
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
        self.ext = os.path.splitext(filename)[1].lower()

        self.src_path = join(settings['source'], path, filename)
        self.dst_path = join(settings['destination'], path, filename)

        self.thumb_name = get_thumb(self.settings, self.filename)
        self.thumb_path = join(settings['destination'], path, self.thumb_name)

        self.logger = logging.getLogger(__name__)
        self._get_metadata()
        signals.media_initialized.send(self)

    def __repr__(self):
        return "<%s>(%r)" % (self.__class__.__name__, str(self))

    def __unicode__(self):
        return join(self.path, self.filename)

    @property
    def big(self):
        """Path to the original image, if ``keep_orig`` is set (relative to the
        album directory). Copy the file if needed.
        """
        if self.settings['keep_orig']:
            s = self.settings
            if s['use_orig']:
                # The image *is* the original, just use it
                return self.filename
            orig_path = join(s['destination'], self.path, s['orig_dir'])
            check_or_create_dir(orig_path)
            copy(self.src_path, join(orig_path, self.src_filename),
                 symlink=s['orig_link'])
            return url_from_path(join(s['orig_dir'], self.src_filename))
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
                          self.settings['thumb_video_delay'],
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

    @cached_property
    def date(self):
        return self.exif and self.exif.get('dateobj', None) or None

    @cached_property
    def exif(self):
        return (get_exif_tags(self.raw_exif)
                if self.raw_exif and self.ext in ('.jpg', '.jpeg') else None)

    @cached_property
    def raw_exif(self):
        try:
            return (get_exif_data(self.src_path)
                    if self.ext in ('.jpg', '.jpeg') else None)
        except (IOError, IndexError, TypeError, AttributeError):
            self.logger.warning(u'Could not read EXIF data from %s',
                                self.src_path)
            return None


class Video(Media):
    """Gather all informations on a video file."""

    type = 'video'
    extensions = ('.mov', '.avi', '.mp4', '.webm', '.ogv')

    def __init__(self, filename, path, settings):
        super(Video, self).__init__(filename, path, settings)
        base = splitext(filename)[0]
        self.date = None
        self.src_filename = filename
        if not settings['use_orig']:
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

    def __init__(self, path, settings, dirnames, filenames, gallery):
        self.path = path
        self.name = path.split(os.path.sep)[-1]
        self.gallery = gallery
        self.settings = settings
        self.output_file = settings['output_filename']
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

        try:
            self.author = self.meta['author'][0]
        except KeyError:
            self.author = self.settings.get('author')

    def create_output_directories(self):
        """Create output directories for thumbnails and original images."""
        check_or_create_dir(self.dst_path)

        if self.medias:
            check_or_create_dir(join(self.dst_path,
                                     self.settings['thumb_dir']))

        if self.medias and self.settings['keep_orig']:
            self.orig_path = join(self.dst_path, self.settings['orig_dir'])
            check_or_create_dir(self.orig_path)

    def sort_medias(self, medias_sort_attr):
        if self.medias:
            if medias_sort_attr == 'date':
                key = lambda s: s.date or datetime.now()
            else:
                key = lambda s: strxfrm(getattr(s, medias_sort_attr))

            self.medias.sort(key=key,
                             reverse=self.settings['medias_sort_reverse'])

        signals.medias_sorted.send(self)

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
            attr = ('src_path' if self.settings['zip_media_format'] == 'orig'
                    else 'dst_path')

            for p in self:
                path = getattr(p, attr)
                try:
                    archive.write(path, os.path.split(path)[1])
                except OSError as e:
                    self.logger.warn('Failed to add %s to the ZIP: %s', p, e)

            archive.close()
            self.logger.debug('Created ZIP archive %s', archive_path)
            return zip_gallery
        else:
            return None


class Gallery(object):

    def __init__(self, settings, ncpu=None):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.stats = defaultdict(int)
        self.init_pool(ncpu)
        check_or_create_dir(settings['destination'])

        # Build the list of directories with images
        albums = self.albums = {}
        src_path = self.settings['source']

        ignore_dirs = settings['ignore_directories']
        ignore_files = settings['ignore_files']

        progressChars = cycle(["/", "-", "\\", "|"])
        if self.logger.getEffectiveLevel() >= logging.WARNING:
            self.progressbar_target = None
        else:
            self.progressbar_target = Devnull()

        for path, dirs, files in os.walk(src_path, followlinks=True,
                                         topdown=False):
            if self.logger.getEffectiveLevel() >= logging.WARNING:
                print("\rCollecting albums " + next(progressChars), end="")
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

        with progressbar(albums.values(), label="Sorting media",
                         file=self.progressbar_target) as progress_albums:
            for album in progress_albums:
                album.sort_medias(settings['medias_sort_attr'])

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

        def log_func(x):
            # 63 is the total length of progressbar, label, percentage, etc
            available_length = get_terminal_size()[0] - 64
            if x and available_length > 10:
                text = text_type(x.name)[:available_length]
                if PY2:
                    text = text.encode('utf-8')
                return text
            else:
                return ""

        try:
            with progressbar(self.albums.values(), label="Collecting files",
                             item_show_func=log_func, show_eta=False,
                             file=self.progressbar_target) as albums:
                media_list = [f for album in albums
                              for f in self.process_dir(album, force=force)]
        except KeyboardInterrupt:
            sys.exit('Interrupted')

        bar_opt = {'label': "Processing files",
                   'show_pos': True,
                   'file': self.progressbar_target}
        failed_files = []

        if self.pool:
            try:
                with progressbar(length=len(media_list), **bar_opt) as bar:
                    for res in self.pool.imap_unordered(worker, media_list):
                        if res:
                            failed_files.append(res)
                        next(bar)
                self.pool.close()
                self.pool.join()
            except KeyboardInterrupt:
                self.pool.terminate()
                sys.exit('Interrupted')
            except pickle.PicklingError:
                self.logger.critical(
                    "Failed to process files with the multiprocessing feature."
                    " This can be caused by some module import or object "
                    "defined in the settings file, which can't be serialized.",
                    exc_info=True)
                sys.exit('Abort')
        else:
            with progressbar(media_list, **bar_opt) as medias:
                for media_item in medias:
                    res = process_file(media_item)
                    if res:
                        failed_files.append(res)

        if failed_files:
            self.remove_files(failed_files)
        print('')

        if self.settings['write_html']:
            writer = Writer(self.settings, index_title=self.title)
            for album in self.albums.values():
                writer.write(album)

        signals.gallery_build.send(self)

    def remove_files(self, files):
        self.logger.error('Some files have failed to be processed:')
        for path, filename in files:
            self.logger.error('  - %s/%s', path, filename)
            album = self.albums[path]
            for f in album.medias:
                if f.filename == filename:
                    self.stats[f.type + '_failed'] += 1
                    album.medias.remove(f)
                    break
        self.logger.error('You can run sigal in verbose (--verbose) or debug '
                          '(--debug) mode to get more details.')

    def process_dir(self, album, force=False):
        """Process a list of images in a directory."""
        for f in album:
            if isfile(f.dst_path) and not force:
                self.logger.info("%s exists - skipping", f.filename)
                self.stats[f.type + '_skipped'] += 1
            else:
                self.stats[f.type] += 1
                yield (f.type, f.path, f.filename, f.src_path, album.dst_path,
                       self.settings)


def process_file(args):
    # args => ftype, path, filename, src_path, dst_path, settings
    processor = process_image if args[0] == 'image' else process_video
    ret = processor(*args[3:])
    # If the processor return an error (ret != 0), then we return the path and
    # filename of the failed file to the parent process.
    return args[1:3] if ret else None


def worker(args):
    try:
        return process_file(args)
    except KeyboardInterrupt:
        pass
