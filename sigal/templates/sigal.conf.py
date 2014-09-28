# -*- coding: utf-8 -*-
#
# All configuration values have a default; values that are commented out serve
# to show the default. Default values are specified when modified in this
# example config file

# Gallery title. Can be set here or as the '--title' option of the `sigal
# build` command, or in the 'index.md' file of the source directory.
# The priority order is: cli option > settings file > index.md file
# title = "Sigal test gallery"

# Source directory. Can be set here or as the first argument of the `sigal
# build` command
source = 'pictures'

# Destination directory. Can be set here or as the second argument of the
# `sigal build` command (default: '_build')
# destination = '_build'

# Theme :
# - colorbox (default), galleria, or the path to a custom theme directory
theme = 'galleria'

# Size of resized image (default: (640, 480))
img_size = (800, 600)

# Pilkit processor used to resize the image
# (see http://pilkit.readthedocs.org/en/latest/#processors)
# - ResizeToFit: fit the image within the specified dimensions (default)
# - ResizeToFill: crop THE IMAGE it to the exact specified width and height
# - SmartResize: identical to ResizeToFill, but uses entropy to crop the image
# - None: don't resize
# img_processor = 'ResizeToFit'

# Generate thumbnails
# make_thumbs = True

# Subdirectory of the thumbnails
# thumb_dir = 'thumbnails'

# Prefix and/or suffix for thumbnail filenames (default: '')
# thumb_prefix = ''
# thumb_suffix = '.tn'

# Thumbnail size (default: (200, 150))
# For the galleria theme, use 280 px for the width
# For the colorbox theme, use 200 px for the width
thumb_size = (280, 210)

# Crop the image to fill the box
# thumb_fit = True

# Keep original image (default: False)
# keep_orig = True

# Subdirectory for original images
# orig_dir = 'original'

# Use symbolic links instead of copying the original images
# orig_link = False

# Reverse sort for albums
# albums_sort_reverse = False

# Attribute of Media objects which is used to sort medias. 'date' can be used
# to sort with EXIF dates.
# medias_sort_attr = 'filename'

# Reverse sort for medias
# medias_sort_reverse = False

# Filter directories and files.
# The settings take a list of patterns matched with the fnmatch module on the
# path relative to the source directory:
# http://docs.python.org/2/library/fnmatch.html
ignore_directories = []
ignore_files = []

# Jpeg options
# jpg_options = {'quality': 85,
#                'optimize': True,
#                'progressive': True}

# Webm options
# Options used in ffmpeg to encode the webm video. You may want to read
# http://ffmpeg.org/trac/ffmpeg/wiki/vpxEncodingGuide
# Be aware of the fact these options need to be passed as strings. If you are
# using avconv (for example with Ubuntu), you will need to adapt the settings.
# webm_options = ['-crf', '10', '-b:v', '1.6M',
#                 '-qmin', '4', '-qmax', '63']

# Size of resized video (default: (480, 360))
# video_size = (480, 360)

# Write HTML files. If False, sigal will only process the images.
# write_html = True

# Name of the generated HTML files
# output_filename = 'index.html'

# Add output filename (see above) to the URLs
# index_in_url = False

# A list of links (tuples (title, URL))
# links = [('Example link', 'http://example.org'),
#          ('Another link', 'http://example.org')]

# Google Analytics tracking code (UA-xxxx-x)
# google_analytics = ''

# Set zip_gallery to either False or a file name. The final archive will
# contain all resized or original files (depending on `zip_media_format`).
# zip_gallery = False   # False or 'archive.zip'
# zip_media_format = 'resized'  # 'resized' or 'orig'

# Autorotate images
# Warning: this setting is not compatible with `copy_exif_data` (see below),
# because Sigal can't save the modified Orientation tag (currently Pillow can't
# write EXIF).
# autorotate_images = True

# If True, EXIF data from the original image is copied to the resized image
# copy_exif_data = False

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
# plugins = ['sigal.plugins.adjust', 'sigal.plugins.copyright']

# Add a copyright text on the image (default: '')
# copyright = "© An example copyright message"

# Adjust the image after resizing it. A default value of 1.0 leaves the images
# untouched.
# adjust_options = {'color': 1.0,
#                   'brightness': 1.0,
#                   'contrast': 1.0,
#                   'sharpness': 1.0}
