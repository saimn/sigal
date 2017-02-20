# -*- coding: utf-8 -*-
#
# All configuration values have a default; values that are commented out serve
# to show the default. Default values are specified when modified in this
# example config file

# Gallery title. Can be set here or as the '--title' option of the `sigal
# build` command, or in the 'index.md' file of the source directory.
# The priority order is: cli option > settings file > index.md file
# title = "Sigal test gallery"

# ---------------------
# General configuration
# ---------------------

# Source directory. Can be set here or as the first argument of the `sigal
# build` command
source = 'pictures'

# Destination directory. Can be set here or as the second argument of the
# `sigal build` command (default: '_build')
# destination = '_build'

# Theme :
# - colorbox (default), galleria, photoswipe, or the path to a custom theme
# directory
theme = 'galleria'

# Author. Used in the footer of the pages and in the author meta tag.
# author = ''

# Use originals in gallery (default: False). If True, this will bypass all
# processing steps (resize, auto-orient, recompress, and any plugin-specific
# step).
# Originals will be symlinked if orig_link = True, else they will be copied.
# use_orig = False

# ----------------
# Image processing (ignored if use_orig = True)
# ----------------

# Size of resized image (default: (640, 480))
img_size = (800, 600)

# Show a map of the images where possible?
# This option only has an effect on the galleria theme for the while.
# The leaflet_provider setting allow to customize the tile provider (see
# https://github.com/leaflet-extras/leaflet-providers#providers)
# show_map = False
# leaflet_provider = 'OpenStreetMap.Mapnik'

# Pilkit processor used to resize the image
# (see http://pilkit.readthedocs.org/en/latest/#processors)
# - ResizeToFit: fit the image within the specified dimensions (default)
# - ResizeToFill: crop THE IMAGE it to the exact specified width and height
# - SmartResize: identical to ResizeToFill, but uses entropy to crop the image
# - None: don't resize
# img_processor = 'ResizeToFit'

# Autorotate images
# Warning: this setting is not compatible with `copy_exif_data` (see below),
# because Sigal can't save the modified Orientation tag (currently Pillow can't
# write EXIF).
# autorotate_images = True

# If True, EXIF data from the original image is copied to the resized image
# copy_exif_data = False

# Jpeg options
# jpg_options = {'quality': 85,
#                'optimize': True,
#                'progressive': True}

# --------------------
# Thumbnail generation
# --------------------

# Generate thumbnails
# make_thumbs = True

# Subdirectory of the thumbnails
# thumb_dir = 'thumbnails'

# Prefix and/or suffix for thumbnail filenames (default: '')
# thumb_prefix = ''
# thumb_suffix = '.tn'

# Thumbnail size (default: (200, 150))
# For the galleria theme, use 280 px for the width
# For the colorbox and photoswipe theme, use 200 px for the width
thumb_size = (280, 210)

# Crop the image to fill the box
# thumb_fit = True

# Delay in seconds to avoid black thumbnails in videos with fade-in
# thumb_video_delay = '0'

# Keep original image (default: False)
# keep_orig = True

# Subdirectory for original images
# orig_dir = 'original'

# Use symbolic links instead of copying the original images
# orig_link = False

# Attribute of Album objects which is used to sort medias (eg 'title'). To sort
# on a metadata key, use 'meta.key'.
# albums_sort_attr = 'name'

# Reverse sort for albums
# albums_sort_reverse = False

# Attribute of Media objects which is used to sort medias. 'date' can be used
# to sort with EXIF dates, and 'meta.key' to sort on a metadata key (which then
# must exist for all images).
# medias_sort_attr = 'filename'

# Reverse sort for medias
# medias_sort_reverse = False

# Filter directories and files.
# The settings take a list of patterns matched with the fnmatch module on the
# path relative to the source directory:
# http://docs.python.org/2/library/fnmatch.html
ignore_directories = []
ignore_files = []

# -------------
# Video options
# -------------

# Video format
# specify an alternative format, valid are 'webm' (default) and 'mp4'
# video_format = 'webm'

# Webm options
# Options used in ffmpeg to encode the webm video. You may want to read
# http://ffmpeg.org/trac/ffmpeg/wiki/vpxEncodingGuide
# Be aware of the fact these options need to be passed as strings. If you are
# using avconv (for example with Ubuntu), you will need to adapt the settings.
# webm_options = ['-crf', '10', '-b:v', '1.6M',
#                 '-qmin', '4', '-qmax', '63']

# MP4 options
# Options used to encode the mp4 video. You may want to read
# https://trac.ffmpeg.org/wiki/Encode/H.264
# mp4_options = ['-crf', '23' ]

# Size of resized video (default: (480, 360))
# video_size = (480, 360)

# -------------
# Miscellaneous
# -------------

# Write HTML files. If False, sigal will only process the images.
# write_html = True

# Name of the generated HTML files
# output_filename = 'index.html'

# Add output filename (see above) to the URLs
# index_in_url = False

# Use CDN for assets (Google fonts, JQuery).
# If False some fonts may not be available.
# use_assets_cdn = True

# A list of links (tuples (title, URL))
# links = [('Example link', 'http://example.org'),
#          ('Another link', 'http://example.org')]

# Google Analytics tracking code (UA-xxxx-x)
# google_analytics = ''

# Google Tag Manager tracking code (GTM-xxxxxx)
# google_tag_manager = ''

# Piwik tracking
# tracker_url must not contain trailing slash.
# Example : {'tracker_url': 'http://stats.domain.com', 'site_id' : 2}
# piwik = {'tracker_url': '', 'site_id' : 0}

# Set zip_gallery to either False or a file name. The file name can be formated
# python style with an 'album' variable, for example '{album.name}.zip'. The final archive will
# contain all resized or original files (depending on `zip_media_format`).
# zip_gallery = False   # False or 'archive.zip'
# zip_media_format = 'resized'  # 'resized' or 'orig'

# Specify a different locale. If set to '', the default locale is used.
# locale = ''

# List of files to copy from the source directory to the destination.
# A symbolic link is used if ``orig_link`` is set to True (see above).
# files_to_copy = (('extra/robots.txt', 'robots.txt'),
#                  ('extra/favicon.ico', 'favicon.ico'),)

# Colorbox theme config
# The column size is given in number of column of the css grid of the Skeleton
# framework which is used for this theme: http://www.getskeleton.com/#grid
# Then the image size must be adapted to fit the column size.
# The default is 4 columns which gives 220px. 3 columns gives 160px.
# colorbox_column_size = 4

# --------
# Plugins
# --------

# List of plugins to use. The values must be a path than can be imported.
# Another option is to import the plugin and put the module in the list, but
# this will break with the multiprocessing feature (the settings dict obtained
# from this file must be serializable).
# plugins = ['sigal.plugins.adjust', 'sigal.plugins.copyright',
#            'sigal.plugins.upload_s3', 'sigal.plugins.media_page',
#            'sigal.plugins.nomedia', 'sigal.plugins.extended_caching']

# Add a copyright text on the image (default: '')
# copyright = "© An example copyright message"

# Adjust the image after resizing it. A default value of 1.0 leaves the images
# untouched.
# adjust_options = {'color': 1.0,
#                   'brightness': 1.0,
#                   'contrast': 1.0,
#                   'sharpness': 1.0}

# Settings for upload to s3 plugin
# upload_s3_options = {
# 	'bucket': 'my-bucket',
# 	'policy': 'public-read',
# 	'overwrite': False
# }
