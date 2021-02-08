# Copyright (c) 2009-2020 - Simon Conseil
# Copyright (c) 2013      - Christophe-Marie Duquesne
# Copyright (c) 2017      - Mate Lakat
# Copyright (c) 2021      - Keith Feldman

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
from os.path import abspath, isabs, join, normpath
from pprint import pformat

_DEFAULT_CONFIG = {
    'albums_sort_attr': 'name',
    'albums_sort_reverse': False,
    'autorotate_images': True,
    'colorbox_column_size': 3,
    'copy_exif_data': False,
    'datetime_format': '%c',
    'destination': '_build',
    'files_to_copy': (),
    'galleria_theme': 'classic',
    'google_analytics': '',
    'google_tag_manager': '',
    'ignore_directories': [],
    'ignore_files': [],
    'img_extensions': ['.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff'],
    'img_processor': 'ResizeToFit',
    'img_size': (640, 480),
    'img_format': None,
    'index_in_url': False,
    'jpg_options': {'quality': 85, 'optimize': True, 'progressive': True},
    'keep_orig': False,
    'html_language': 'en',
    'leaflet_provider': 'OpenStreetMap.Mapnik',
    'links': '',
    'locale': '',
    'make_thumbs': True,
    'medias_sort_attr': 'filename',
    'medias_sort_reverse': False,
    'mp4_options': ['-crf', '23', '-strict', '-2'],
    'mp4_options_second_pass': None,
    'orig_dir': 'original',
    'orig_link': False,
    'rel_link': False,
    'output_filename': 'index.html',
    'piwik': {'tracker_url': '', 'site_id': 0},
    'plugin_paths': [],
    'plugins': [],
    'site_logo': '',
    'show_map': False,
    'source': '',
    'theme': 'colorbox',
    'thumb_dir': 'thumbnails',
    'thumb_fit': True,
    'thumb_fit_centering': (0.5, 0.5),
    'thumb_prefix': '',
    'thumb_size': (200, 150),
    'thumb_suffix': '',
    'thumb_video_delay': '0',
    'title': '',
    'use_orig': False,
    'user_css': None,
    'video_converter': 'ffmpeg',
    'video_extensions': ['.mov', '.avi', '.mp4', '.webm', '.ogv', '.3gp'],
    'video_format': 'webm',
    'video_always_convert': False,
    'video_size': (480, 360),
    'watermark': '',
    'webm_options': ['-crf', '10', '-b:v', '1.6M',
                     '-qmin', '4', '-qmax', '63'],
    'webm_options_second_pass': None,
    'write_html': True,
    'zip_gallery': False,
    'zip_media_format': 'resized',
}


class Status:
    SUCCESS = 0
    FAILURE = 1


def get_thumb(settings, filename):
    """Return the path to the thumb.

    examples:
    >>> default_settings = create_settings()
    >>> get_thumb(default_settings, "bar/foo.jpg")
    "bar/thumbnails/foo.jpg"
    >>> get_thumb(default_settings, "bar/foo.png")
    "bar/thumbnails/foo.png"

    for videos, it returns a jpg file:
    >>> get_thumb(default_settings, "bar/foo.webm")
    "bar/thumbnails/foo.jpg"
    """

    path, filen = os.path.split(filename)
    name, ext = os.path.splitext(filen)

    if ext.lower() in settings['video_extensions']:
        ext = '.jpg'
    return join(path, settings['thumb_dir'], settings['thumb_prefix'] +
                name + settings['thumb_suffix'] + ext)


def read_settings(filename=None):
    """Read settings from a config file in the source_dir root."""

    logger = logging.getLogger(__name__)
    logger.info("Reading settings ...")
    settings = _DEFAULT_CONFIG.copy()

    if filename:
        logger.debug("Settings file: %s", filename)
        settings_path = os.path.dirname(filename)
        tempdict = {}

        with open(filename) as f:
            code = compile(f.read(), filename, 'exec')
            exec(code, tempdict)

        settings.update((k, v) for k, v in tempdict.items()
                        if k not in ['__builtins__'])

        # Make the paths relative to the settings file
        paths = ['source', 'destination', 'watermark']

        if os.path.isdir(join(settings_path, settings['theme'])) and \
                os.path.isdir(join(settings_path, settings['theme'],
                                   'templates')):
            paths.append('theme')

        for p in paths:
            path = settings[p]
            if path and not isabs(path):
                settings[p] = abspath(normpath(join(settings_path, path)))
                logger.debug("Rewrite %s : %s -> %s", p, path, settings[p])

    for key in ('img_size', 'thumb_size', 'video_size'):
        w, h = settings[key]
        if h > w:
            settings[key] = (h, w)
            logger.warning("The %s setting should be specified with the "
                           "largest value first.", key)

    if not settings['img_processor']:
        logger.info('No Processor, images will not be resized')

    logger.debug('Settings:\n%s', pformat(settings, width=120))
    return settings


def create_settings(**kwargs):
    """Create a new default setting copy and initialize it with kwargs."""
    settings = _DEFAULT_CONFIG.copy()
    settings.update(kwargs)
    return settings
