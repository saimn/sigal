"""Plugin to upload generated files to Amazon S3.

This plugin requires boto_. All generated files are uploaded to a specified S3
bucket.  When using this plugin you have to make sure that the bucket already
exists and the you have access to the S3 bucket. The access credentials are
managed by boto_ and can be given as environment variables, configuration files
etc. More information can be found on the boto_ documentation.

.. _boto: https://pypi.org/project/boto/

Settings (all settings are wrapped in ``upload_s3_options`` dict):

- ``bucket``: The to-be-used bucket for uploading.
- ``policy``: Specifying access control to the uploaded files. Possible values:
  private, public-read, public-read-write, authenticated-read
- ``overwrite``: Boolean indicating if all files should be uploaded and
  overwritten or if already uploaded files should be skipped.
- ``max_age``: Optional, Integer indicating the number of seconds that the
  cache control should be set by default
- ``media_max_age``: Optional, Integer indicates the number of seconds that
  cache control hould be set for media files

"""

import logging
import os

import boto
from boto.s3.key import Key
from click import progressbar

from sigal import signals

logger = logging.getLogger(__name__)


def upload_s3(gallery, settings=None):
    upload_files = []

    # Get local files
    for root, dirs, files in os.walk(gallery.settings['destination']):
        for f in files:
            path = os.path.join(
                root[len(gallery.settings['destination']) + 1:], f)
            size = os.path.getsize(os.path.join(root, f))
            upload_files += [(path, size)]

    # Connect to specified bucket
    conn = boto.connect_s3()
    bucket = conn.get_bucket(gallery.settings['upload_s3_options']['bucket'])

    # Upload the files
    with progressbar(upload_files, label="Uploading files to S3") as bar:
        for (f, size) in bar:
            if gallery.settings['upload_s3_options']['overwrite'] is False:
                # Check if file was uploaded before
                key = bucket.get_key(f)
                if key is not None and key.size == size:
                    cache_metadata = generate_cache_metadata(gallery, f)

                    if key.get_metadata('Cache-Control') != cache_metadata:
                        key.set_remote_metadata({
                            'Cache-Control': cache_metadata}, {}, True)
                    logger.debug("Skipping file %s" % (f))
                else:
                    upload_file(gallery, bucket, f)
            else:
                # File is not available on S3 yet
                upload_file(gallery, bucket, f)


def generate_cache_metadata(gallery, f):
    filename, file_extension = os.path.splitext(f)

    proposed_cache_control = None
    if 'media_max_age' in gallery.settings['upload_s3_options'] and \
            file_extension in ['.jpg', '.png', '.webm', '.mp4']:
        proposed_cache_control = "max-age=%s" % \
            gallery.settings['upload_s3_options']['media_max_age']
    elif 'max_age' in gallery.settings['upload_s3_options']:
        proposed_cache_control = "max-age=%s" % \
            gallery.settings['upload_s3_options']['max_age']
    return proposed_cache_control


def upload_file(gallery, bucket, f):
    logger.debug("Uploading file %s" % (f))

    key = Key(bucket)
    key.key = f

    cache_metadata = generate_cache_metadata(gallery, f)
    if cache_metadata:
        key.set_metadata('Cache-Control', cache_metadata)

    key.set_contents_from_filename(
        os.path.join(gallery.settings['destination'], f),
        policy=gallery.settings['upload_s3_options']['policy'])


def register(settings):
    if settings.get('upload_s3_options'):
        signals.gallery_build.connect(upload_s3)
    else:
        logger.warning('Upload to S3 is not configured.')
