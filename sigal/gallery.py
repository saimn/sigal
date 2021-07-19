# Copyright (c) 2009-2020 - Simon Conseil
# Copyright (c) 2013      - Christophe-Marie Duquesne
# Copyright (c) 2014      - Jonas Kaufmann
# Copyright (c) 2015      - François D.
# Copyright (c) 2017      - Mate Lakat
# Copyright (c) 2018      - Edwin Steele

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

import fnmatch
import logging
import multiprocessing
import os
import pickle
import random
import sys
from collections import defaultdict
from datetime import datetime
from itertools import cycle
from os.path import isfile, join, splitext
from urllib.parse import quote as url_quote

from click import get_terminal_size, progressbar
from natsort import natsort_keygen, ns
from PIL import Image as PILImage

from . import image, signals, video
from .cache import Cache
from .image import get_exif_tags, get_image_metadata, get_size, process_image
from .settings import Status, get_thumb
from .utils import (
    Devnull,
    cached_property,
    check_or_create_dir,
    copy,
    get_mime,
    get_mod_date,
    is_valid_html5_video,
    read_markdown,
    url_from_path,
)
from .video import process_video
from .writer import AlbumListPageWriter, AlbumPageWriter


# metadata cache
CACHE = None


class Media:
    """Base Class for media files.

    Attributes:

    :var Media.type: ``"image"`` or ``"video"``.
    :var Media.dst_filename: Filename of the resized image.
    :var Media.thumbnail: Location of the corresponding thumbnail image.
    :var Media.big: If not None, location of the unmodified image.
    :var Media.big_url: If not None, url of the unmodified image.

    """

    type = ''
    """Type of media, e.g. ``"image"`` or ``"video"``."""

    def __init__(self, filename, path, settings):
        self.path = path
        self.settings = settings

        self.basename = os.path.splitext(filename)[0]

        self.dst_filename = filename
        """Filename of the resized image."""

        self.src_filename = filename
        """Filename of the input image."""

        self.src_ext = os.path.splitext(filename)[1].lower()
        """Input extension."""

        self.src_path = join(settings['source'], path, self.src_filename)

        self.thumb_name = get_thumb(self.settings, self.dst_filename)

        self.logger = logging.getLogger(__name__)

        self.file_metadata = None
        self._get_metadata()

        # default: title is the filename
        if not self.title:
            self.title = self.basename
        signals.media_initialized.send(self)

    def __repr__(self):
        return f"<{self.__class__.__name__}>({str(self)!r})"

    def __str__(self):
        return join(self.path, self.src_filename)

    def __getstate__(self):
        state = self.__dict__.copy()
        # remove un-pickable objects
        state['logger'] = None
        return state

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)
        self.logger = logging.getLogger(__name__)

    @property
    def dst_path(self):
        return join(self.settings['destination'], self.path, self.dst_filename)

    @property
    def thumb_path(self):
        return join(self.settings['destination'], self.path, self.thumb_name)

    @property
    def url(self):
        """URL of the media."""
        return url_from_path(self.dst_filename)

    @property
    def big(self):
        """Path to the original image, if ``keep_orig`` is set (relative to the
        album directory). Copy the file if needed.
        """
        if self.settings['keep_orig']:
            s = self.settings
            if s['use_orig']:
                # The image *is* the original, just use it
                return self.src_filename
            orig_path = join(s['destination'], self.path, s['orig_dir'])
            check_or_create_dir(orig_path)
            big_path = join(orig_path, self.src_filename)
            if not isfile(big_path):
                copy(
                    self.src_path,
                    big_path,
                    symlink=s['orig_link'],
                    rellink=self.settings['rel_link'],
                )
            return join(s['orig_dir'], self.src_filename)

    @property
    def big_url(self):
        """URL of the original media."""
        if self.big is not None:
            return url_from_path(self.big)

    @property
    def thumbnail(self):
        """Path to the thumbnail image (relative to the album directory)."""

        if not isfile(self.thumb_path):
            self.logger.debug('Generating thumbnail for %r', self)
            path = self.dst_path if os.path.exists(self.dst_path) else self.src_path
            try:
                # if thumbnail is missing (if settings['make_thumbs'] is False)
                s = self.settings
                if self.type == 'image':
                    image.generate_thumbnail(
                        path, self.thumb_path, s['thumb_size'], fit=s['thumb_fit']
                    )
                elif self.type == 'video':
                    video.generate_thumbnail(
                        path,
                        self.thumb_path,
                        s['thumb_size'],
                        s['thumb_video_delay'],
                        fit=s['thumb_fit'],
                        converter=s['video_converter'],
                    )
            except Exception as e:
                self.logger.error('Failed to generate thumbnail: %s', e)
                return
        return url_from_path(self.thumb_name)

    def _get_metadata(self):
        """Get image metadata from filename.md: title, description, meta."""

        self.description = ''
        """Description extracted from the Markdown <imagename>.md file."""

        self.title = ''
        """Title extracted from the Markdown <imagename>.md file."""

        self.meta = {}
        """Other metadata extracted from the Markdown <imagename>.md file."""

        descfile = splitext(self.src_path)[0] + '.md'
        if isfile(descfile):
            meta = None
            if CACHE:
                meta = CACHE.read_dict(descfile)
            if not meta:
                meta = read_markdown(descfile)
                if CACHE:
                    CACHE.write_dict(descfile, meta)
            for key, val in meta.items():
                setattr(self, key, val)

    def _get_file_date(self):
        return datetime.fromtimestamp(get_mod_date(self.src_path))


class Image(Media):
    """Gather all informations on an image file."""

    type = 'image'

    def __init__(self, filename, path, settings):
        super().__init__(filename, path, settings)
        imgformat = settings.get('img_format')

        if imgformat and PILImage.EXTENSION[self.src_ext] != imgformat.upper():
            # Find the extension that should match img_format
            extensions = {v: k for k, v in PILImage.EXTENSION.items()}
            ext = extensions[imgformat.upper()]
            self.dst_filename = self.basename + ext
            self.thumb_name = get_thumb(self.settings, self.dst_filename)

    @cached_property
    def date(self):
        """The date from the EXIF DateTimeOriginal metadata if available, or
        from the file date."""
        return self.exif and self.exif.get('dateobj', None) or self._get_file_date()

    @cached_property
    def exif(self):
        """If not `None` contains a dict with the most common tags. For more
        information, see :ref:`simple-exif-data`.
        """
        datetime_format = self.settings['datetime_format']
        return (
            get_exif_tags(self.raw_exif, datetime_format=datetime_format)
            if self.raw_exif and self.src_ext in ('.jpg', '.jpeg')
            else None
        )

    def _get_metadata(self):
        super()._get_metadata()

        meta = None
        if CACHE:
            meta = CACHE.read_dict(self.src_path)
        if not meta:
            meta = get_image_metadata(self.src_path)
            if CACHE:
                CACHE.write_dict(self.src_path, meta)
        self.file_metadata = meta

        # If a title or description hasn't been obtained by other means, look
        #  for the information in IPTC fields
        if self.title and self.description:
            # Nothing to do - we already have title and description
            return

        iptc_data = self.file_metadata['iptc']
        if not self.title and iptc_data.get('title'):
            self.title = iptc_data['title']
        if not self.description and iptc_data.get('description'):
            self.description = iptc_data['description']

    @cached_property
    def raw_exif(self):
        """If not `None`, contains the raw EXIF tags."""
        if self.src_ext in ('.jpg', '.jpeg'):
            return self.file_metadata['exif']

    @cached_property
    def size(self):
        """The dimensions of the resized image."""
        return get_size(self.dst_path)

    @cached_property
    def input_size(self):
        """The dimensions of the input image."""
        return get_size(self.src_path)

    @cached_property
    def thumb_size(self):
        """The dimensions of the thumbnail image."""
        return get_size(self.thumb_path)

    def has_location(self):
        """True if location information is available for EXIF GPSInfo."""
        return self.exif is not None and 'gps' in self.exif


class Video(Media):
    """Gather all informations on a video file."""

    type = 'video'

    def __init__(self, filename, path, settings):
        super().__init__(filename, path, settings)
        self.date = self._get_file_date()

        if not settings['use_orig'] or not is_valid_html5_video(self.src_ext):
            video_format = settings['video_format']
            ext = '.' + video_format
            self.dst_filename = self.basename + ext
            self.mime = get_mime(ext)
        else:
            self.mime = get_mime(self.src_ext)


class Album:
    """Gather all informations on an album.

    Attributes:

    :var description_file: Name of the Markdown file which gives information
        on an album
    :var index_url: URL to the index page.
    :var output_file: Name of the output HTML file
    :var meta: Meta data from the Markdown file.
    :var description: description from the Markdown file.

    For details how to annotate your albums with meta data, see
    :doc:`album_information`.

    """

    description_file = "index.md"

    def __init__(self, path, settings, dirnames, filenames, gallery):
        self.path = path
        self.name = path.split(os.path.sep)[-1]
        self.gallery = gallery
        self.settings = settings
        self.subdirs = dirnames
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

        self.index_url = (
            url_from_path(os.path.relpath(settings['destination'], self.dst_path))
            + '/'
            + self.url_ext
        )

        #: List of all medias in the album (:class:`~sigal.gallery.Image` and
        #: :class:`~sigal.gallery.Video`).
        self.medias = medias = []
        self.medias_count = defaultdict(int)

        for f in filenames:
            ext = splitext(f)[1]
            media = None
            if ext.lower() in settings['img_extensions']:
                media = Image(f, self.path, settings)
            elif ext.lower() in settings['video_extensions']:
                media = Video(f, self.path, settings)

            # Allow modification of the media, including overriding the class
            # type for the media.
            result = signals.album_file.send(self, filename=f, media=media)
            for recv, ret in result:
                if ret is not None:
                    media = ret

            if media:
                self.medias_count[media.type] += 1
                medias.append(media)

        signals.album_initialized.send(self)

    def __repr__(self):
        return "<{}>(path={!r}, title={!r})".format(
            self.__class__.__name__, self.path, self.title
        )

    def __str__(self):
        return f'{self.path} : ' + ', '.join(
            f'{count} {_type}s' for _type, count in self.medias_count.items()
        )

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
        self.title = os.path.basename(self.path if self.path != '.' else self.src_path)

        if isfile(descfile):
            meta = None
            if CACHE:
                meta = CACHE.read_dict(descfile)
            if not meta:
                meta = read_markdown(descfile)
                if CACHE:
                    CACHE.write_dict(descfile, meta)
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
            check_or_create_dir(join(self.dst_path, self.settings['thumb_dir']))

        if self.medias and self.settings['keep_orig']:
            self.orig_path = join(self.dst_path, self.settings['orig_dir'])
            check_or_create_dir(self.orig_path)

    def sort_subdirs(self, albums_sort_attr):
        if self.subdirs:
            if not albums_sort_attr:
                albums_sort_attr = self.settings['albums_sort_attr']
            reverse = self.settings['albums_sort_reverse']

            if 'sort' in self.meta:
                albums_sort_attr = self.meta['sort'][0]
                if albums_sort_attr[0] == '-':
                    albums_sort_attr = albums_sort_attr[1:]
                    reverse = True
                else:
                    reverse = False

            root_path = self.path if self.path != '.' else ''
            if albums_sort_attr.startswith("meta."):
                meta_key = albums_sort_attr.split(".", 1)[1]

                def sort_key(s):
                    album = self.gallery.albums[join(root_path, s)]
                    return album.meta.get(meta_key, [''])[0]

            else:

                def sort_key(s):
                    album = self.gallery.albums[join(root_path, s)]
                    return getattr(album, albums_sort_attr)

            key = natsort_keygen(key=sort_key, alg=ns.LOCALE)
            self.subdirs.sort(key=key, reverse=reverse)

        signals.albums_sorted.send(self)

    def sort_medias(self, medias_sort_attr):
        if self.medias:
            if medias_sort_attr == 'filename':
                medias_sort_attr = 'dst_filename'

            if medias_sort_attr == 'date':
                key = lambda s: s.date or datetime.now()
            elif medias_sort_attr.startswith('meta.'):
                meta_key = medias_sort_attr.split(".", 1)[1]
                key = natsort_keygen(
                    key=lambda s: s.meta.get(meta_key, [''])[0], alg=ns.LOCALE
                )
            else:
                key = natsort_keygen(
                    key=lambda s: getattr(s, medias_sort_attr), alg=ns.LOCALE
                )

            self.medias.sort(key=key, reverse=self.settings['medias_sort_reverse'])

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
        return [self.gallery.albums[join(root_path, path)] for path in self.subdirs]

    @property
    def nbmedias(self):
        return len(self.medias) + sum(len(album) for album in self.albums)

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
            return self._thumbnail

        # Test the thumbnail from the Markdown file.
        thumbnail = self.meta.get('thumbnail', [''])[0]

        if thumbnail and isfile(join(self.src_path, thumbnail)):
            self._thumbnail = url_from_path(
                join(self.name, get_thumb(self.settings, thumbnail))
            )
            self.logger.debug("Thumbnail for %r : %s", self, self._thumbnail)
            return self._thumbnail
        else:
            # find and return the first landscape image
            for f in self.medias:
                ext = splitext(f.dst_filename)[1]
                if ext.lower() not in self.settings['img_extensions']:
                    continue

                # Use f.size if available as it is quicker (in cache), but
                # fallback to the size of src_path if dst_path is missing
                size = f.input_size
                if size is None:
                    size = f.file_metadata['size']

                if size['width'] > size['height']:
                    try:
                        self._thumbnail = url_quote(self.name) + '/' + f.thumbnail
                    except Exception as e:
                        self.logger.info(
                            "Failed to get thumbnail for %s: %s", f.dst_filename, e
                        )
                    else:
                        self.logger.debug(
                            "Use 1st landscape image as thumbnail for %r : %s",
                            self,
                            self._thumbnail,
                        )
                        return self._thumbnail

            # else simply return the 1st media file
            if not self._thumbnail and self.medias:
                for media in self.medias:
                    if media.thumbnail is not None:
                        try:
                            self._thumbnail = (
                                url_quote(self.name) + '/' + media.thumbnail
                            )
                        except Exception as e:
                            self.logger.info(
                                "Failed to get thumbnail for %s: %s",
                                media.dst_filename,
                                e,
                            )
                        else:
                            break
                else:
                    self.logger.warning("No thumbnail found for %r", self)
                    return

                self.logger.debug(
                    "Use the 1st image as thumbnail for %r : %s", self, self._thumbnail
                )
                return self._thumbnail

            # use the thumbnail of their sub-directories
            if not self._thumbnail:
                for path, album in self.gallery.get_albums(self.path):
                    if album.thumbnail:
                        self._thumbnail = url_quote(self.name) + '/' + album.thumbnail
                        self.logger.debug(
                            "Using thumbnail from sub-directory for %r : %s",
                            self,
                            self._thumbnail,
                        )
                        return self._thumbnail

        self.logger.error('Thumbnail not found for %r', self)

    @property
    def random_thumbnail(self):
        try:
            return url_from_path(join(self.name, random.choice(self.medias).thumbnail))
        except IndexError:
            return self.thumbnail

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

            url = url_from_path(os.path.relpath(path, self.path)) + '/' + self.url_ext
            breadcrumb.append((url, self.gallery.albums[path].title))

        breadcrumb.reverse()
        return breadcrumb

    @property
    def show_map(self):
        """Check if we have at least one photo with GPS location in the album"""
        return any(image.has_location() for image in self.images)

    @cached_property
    def zip(self):
        """Placeholder ZIP method.
        The ZIP logic is controlled by the zip_gallery plugin
        """


class Gallery:
    def __init__(self, settings, ncpu=None, quiet=False):
        global CACHE
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.stats = defaultdict(int)
        self.init_pool(ncpu)
        check_or_create_dir(settings['destination'])

        if settings['max_img_pixels']:
            PILImage.MAX_IMAGE_PIXELS = settings['max_img_pixels']

        # Build the list of directories with images
        albums = self.albums = {}
        src_path = self.settings['source']

        ignore_dirs = settings['ignore_directories']
        ignore_files = settings['ignore_files']

        progressChars = cycle(["/", "-", "\\", "|"])
        show_progress = (
            not quiet
            and self.logger.getEffectiveLevel() >= logging.WARNING
            and os.isatty(sys.stdout.fileno())
        )
        self.progressbar_target = None if show_progress else Devnull()

        with Cache(settings) as cache:
            CACHE = cache
            for path, dirs, files in os.walk(src_path, followlinks=True, topdown=False):
                if show_progress:
                    print("\rCollecting albums " + next(progressChars), end="")
                relpath = os.path.relpath(path, src_path)

                # Test if the directory match the ignore_dirs settings
                if ignore_dirs and any(
                    fnmatch.fnmatch(relpath, ignore) for ignore in ignore_dirs
                ):
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
        CACHE = None

        if show_progress:
            print("\rCollecting albums, done.")

        with progressbar(
            albums.values(),
            label="%16s" % "Sorting albums",
            file=self.progressbar_target,
        ) as progress_albums:
            for album in progress_albums:
                album.sort_subdirs(settings['albums_sort_attr'])

        with progressbar(
            albums.values(),
            label="%16s" % "Sorting media",
            file=self.progressbar_target,
        ) as progress_albums:
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

            def pool_init():
                if self.settings['max_img_pixels']:
                    PILImage.MAX_IMAGE_PIXELS = self.settings['max_img_pixels']

            self.pool = multiprocessing.Pool(processes=ncpu, initializer=pool_init)
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
                return x.name[:available_length]
            else:
                return ""

        try:
            with progressbar(
                self.albums.values(),
                label="Collecting files",
                item_show_func=log_func,
                show_eta=False,
                file=self.progressbar_target,
            ) as albums:
                media_list = [
                    f for album in albums for f in self.process_dir(album, force=force)
                ]
        except KeyboardInterrupt:
            sys.exit('Interrupted')

        bar_opt = {
            'label': "Processing files",
            'show_pos': True,
            'file': self.progressbar_target,
        }

        if self.pool:
            result = []
            try:
                with progressbar(length=len(media_list), **bar_opt) as bar:
                    for status in self.pool.imap_unordered(worker, media_list):
                        result.append(status)
                        bar.update(1)
            except KeyboardInterrupt:
                self.pool.terminate()
                sys.exit('Interrupted')
            except pickle.PicklingError:
                self.logger.critical(
                    "Failed to process files with the multiprocessing feature."
                    " This can be caused by some module import or object "
                    "defined in the settings file, which can't be serialized.",
                    exc_info=True,
                )
                sys.exit('Abort')
            finally:
                self.pool.close()
                self.pool.join()
        else:
            with progressbar(media_list, **bar_opt) as medias:
                result = [process_file(media_item) for media_item in medias]

        if any(result):
            failed_files = [
                media for status, media in zip(result, media_list) if status != 0
            ]
            self.remove_files(failed_files)

        if self.settings['write_html']:
            album_writer = AlbumPageWriter(self.settings, index_title=self.title)
            album_list_writer = AlbumListPageWriter(
                self.settings, index_title=self.title
            )
            with progressbar(
                self.albums.values(),
                label="%16s" % "Writing files",
                item_show_func=log_func,
                show_eta=False,
                file=self.progressbar_target,
            ) as albums:
                for album in albums:
                    if album.albums:
                        if album.medias:
                            self.logger.warning(
                                "Album %s contains sub-albums and images. "
                                "Please move images to their own sub-album. "
                                "Images in album %s will not be visible.",
                                album.title,
                                album.title,
                            )
                        album_list_writer.write(album)
                    else:
                        album_writer.write(album)
        print('')

        signals.gallery_build.send(self)

    def remove_files(self, medias):
        self.logger.error('Some files have failed to be processed:')
        for media in medias:
            self.logger.error('  - %s', media.dst_filename)
            album = self.albums[media.path]
            for f in album.medias:
                if f.dst_filename == media.dst_filename:
                    self.stats[f.type + '_failed'] += 1
                    album.medias.remove(f)
                    break
        self.logger.error(
            'You can run "sigal build" in verbose (--verbose) or'
            ' debug (--debug) mode to get more details.'
        )

    def process_dir(self, album, force=False):
        """Process a list of images in a directory."""
        for f in album:
            if isfile(f.dst_path) and not force:
                self.logger.info("%s exists - skipping", f.dst_filename)
                self.stats[f.type + '_skipped'] += 1
            else:
                self.stats[f.type] += 1
                yield f


def process_file(media):
    processor = None
    if media.type == 'image':
        processor = process_image
    elif media.type == 'video':
        processor = process_video

    # Allow overriding of the processor
    result = signals.process_file.send(media, processor=processor)
    for recv, ret in result:
        if ret is not None:
            processor = ret

    if processor:
        return processor(media)
    else:
        logging.warning('Processor not found for media %s', media.path)
        return Status.FAILURE


def worker(args):
    try:
        return process_file(args)
    except KeyboardInterrupt:
        pass
