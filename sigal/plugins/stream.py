# -*- coding: utf-8 -*-

"""Plugin which adds a "stream page" listing all images.

This plugin is similar to the feeds plugin in that it allows listing
images in (reverse) chronological order, to show the most recent
ones. This allows users to browse the gallery as a "flat" list of
images, a bit like you would on sites like Flickr or Instagram.

Settigns:

- ``stream_page``, see below

Example::

    stream_page = { 'filename': 'stream.html', 'nb_items': 10, 'title': 'Stream' }

In the above example, a 10-item page will be created at
/stream.html. If any entry is missing, a default will be used as
defined above (except `nb_items` which defaults to no limit.

.. todo:: What happens if an album with the same name exists?

"""

import logging
import os.path

from sigal import signals
from sigal.gallery import Album
from sigal.writer import Writer

logger = logging.getLogger(__name__)


def generate_stream(gallery):
    settings = gallery.settings.get('stream_page', {})
    albums = gallery.albums.values()
    if len(albums) < 1:
        logging.debug('no albums, empty stream')
        return
    # fake meta-album to regroup them all
    feed_album = Album('.', gallery.settings, [], [], gallery)
    feed_album.output_file = settings.get('filename', 'stream.html')
    for album in albums:
        feed_album.merge(album)
    feed_album = feed_album.flatten()
    nb_medias = len(feed_album.medias)
    nb_items = settings.get('nb_items', 0)
    nb_items = min(nb_items, nb_medias) if nb_items > 0 else nb_medias
    del feed_album.medias[nb_items:]
    # copy-pasted from feeds.py
    feed_album.medias.sort(key=lambda m: m.date, reverse=True)
    writer = Writer(gallery.settings,
                    index_title=settings.get('title', 'Stream'))
    # copy-pasted from Writer.write()
    path = os.path.join(feed_album.dst_path, feed_album.output_file)
    logger.info('Generating streams page: %s', path)
    writer.write(feed_album)


def register(settings):
    signals.gallery_build.connect(generate_stream)
