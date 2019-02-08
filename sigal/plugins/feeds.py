"""Plugin which add RSS/ATOM feeds.

This plugin requires feedgenerator_. It uses all the images and videos of the
gallery, sorted by date, to show the most recent ones.

.. _feedgenerator: https://pypi.org/project/feedgenerator/

Settings:

- ``rss_feed`` and ``atom_feed``, see below.

Example::

    rss_feed = {'feed_url': 'http://example.org/feed.rss', 'nb_items': 10}
    atom_feed = {'feed_url': 'http://example.org/feed.atom', 'nb_items': 10}

"""

import logging
import os

from datetime import datetime
from feedgenerator import Atom1Feed, Rss201rev2Feed
from jinja2 import Markup
from sigal import signals

logger = logging.getLogger(__name__)


def generate_feeds(gallery):
    # Get all images and videos and sort by date
    medias = [med for album in gallery.albums.values()
              for med in album.medias if med.date is not None]
    medias.sort(key=lambda m: m.date, reverse=True)

    settings = gallery.settings
    if settings.get('rss_feed'):
        generate_feed(gallery, medias, feed_type='rss', **settings['rss_feed'])
    if settings.get('atom_feed'):
        generate_feed(gallery, medias, feed_type='atom',
                      **settings['atom_feed'])


def generate_feed(gallery, medias, feed_type=None, feed_url='', nb_items=0):
    root_album = gallery.albums['.']
    cls = Rss201rev2Feed if feed_type == 'rss' else Atom1Feed
    feed = cls(
        title=Markup.escape(root_album.title),
        link='/',
        feed_url=feed_url,
        description=Markup.escape(root_album.description).striptags()
    )

    theme = gallery.settings['theme']
    nb_medias = len(medias)
    nb_items = min(nb_items, nb_medias) if nb_items > 0 else nb_medias

    for item in medias[:nb_items]:
        if theme == 'galleria':
            link = '%s/%s/#%s' % (feed_url, item.path, item.url)
        else:
            link = '%s/%s/' % (feed_url, item.path)

        feed.add_item(
            title=Markup.escape(item.title or item.url),
            link=link,
            # unique_id='tag:%s,%s:%s' % (urlparse(link).netloc,
            #                             item.date.date(),
            #                             urlparse(link).path.lstrip('/')),
            description='<img src="%s/%s/%s" />' % (feed_url, item.path,
                                                    item.thumbnail),
            # categories=item.tags if hasattr(item, 'tags') else None,
            author_name=getattr(item, 'author', ''),
            pubdate=item.date or datetime.now(),
        )

    output_file = os.path.join(root_album.dst_path, feed_url.split('/')[-1])
    logger.info('Generate %s feeds: %s', feed_type.upper(), output_file)
    with open(output_file, 'w', encoding='utf8') as f:
        feed.write(f, 'utf-8')


def register(settings):
    signals.gallery_build.connect(generate_feeds)
