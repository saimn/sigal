# -*- coding: utf-8 -*-

"""Plugin to upload generated files to Amazon S3.

This plugin requires boto_. All generated files are uploaded to a specified S3 bucket.
When using this plugin you have to make sure that the bucket already exists and the 
you have access to the S3 bucket. The access credentials are managed by boto_ and
can be given as environment variables, configuration files etc. More information
can be found on the boto_ documentation.

.. _boto: https://pypi.python.org/pypi/boto

Settings (all settings are wrapped in ``upload_s3_options`` dict):

- ``bucket``: The to-be-used bucket for uploading.

"""

import logging
import os
from sigal import signals
import boto
from boto.s3.key import Key

logger = logging.getLogger(__name__)


def upload_s3(gallery, settings=None):
    upload_files = []

    for album in gallery.albums.values():
        logger.debug("Processing album: %s" % (album))
        for media in album.medias:
            upload_files.append(os.path.join(album.path, media.filename))
            upload_files.append(os.path.join(album.path, gallery.settings['thumb_dir'], media.filename))

        # generated HTML files
        html_file_upload_path = album.path if album.path != '.' else ''
        upload_files.append(os.path.join(html_file_upload_path, album.output_file))

    # static directory from template
    static_path = os.path.join(gallery.settings['destination'], 'static')
    static_files = [ os.path.join(root[len(gallery.settings['destination'])+1:], name) 
                     for root, dirs, files in os.walk(static_path) 
                     for name in files ]
    upload_files += static_files


    conn = boto.connect_s3()
    bucket = conn.get_bucket(gallery.settings['upload_s3_options']['bucket'])
    for f in upload_files:
        logger.debug("Uploading file %s" % (f))
        key = Key(bucket)
        key.key = f
        key.set_contents_from_filename(os.path.join(gallery.settings['destination'], f))
    return None


def register(settings):
    if settings.get('upload_s3_options'):
        signals.gallery_build.connect(upload_s3)
    else:
        logger.warning('Upload to S3 is not configured.')
