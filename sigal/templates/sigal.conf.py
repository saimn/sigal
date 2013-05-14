# -*- coding: utf-8 -*-
#
# All configuration values have a default; values that are commented out serve
# to show the default. Default values are specified when modified in this
# example config file

# Source directory. Can be set here or as the first argument of the `sigal
# build` command
source = 'pictures'

# Destination directory. Can be set here or as the second argument of the
# `sigal build` command (default: '_build')
# destination = '_build'

# Theme :
# - colorbox (default), galleria, or the path to a custom theme directory
theme = 'galleria'

# Size of resized image
img_size = (800, 600)

# Pilkit processor used to resize the image
# (see http://pilkit.readthedocs.org/en/latest/#processors)
# - ResizeToFit: fit the image within the specified dimensions (default)
# - ResizeToFill: crop THE IMAGE it to the exact specified width and height
# - SmartResize: identical to ResizeToFill, but uses entropy to crop the image
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

# Jpeg options
# jpg_options = {'quality': 85,
#                'optimize': True,
#                'progressive': True}

# Write HTML files. If False, sigal will only process the images.
# write_html = True

# Add index.html to the URLs
# index_in_url = False

# A list of links (tuples (title, URL))
# links = [('Example link', 'http://example.org'),
#          ('Another link', 'http://example.org')]

# Add a copyright text on the image (default: '')
# copyright = "An example copyright message"

# Google Analytics tracking code (UA-xxxx-x)
# google_analytics = ''
