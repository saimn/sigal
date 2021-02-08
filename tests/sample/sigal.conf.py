author = 'John Doe'
title = 'Sigal test gallery ☺'
source = 'pictures'
thumb_suffix = '.tn'
keep_orig = True
thumb_video_delay = 5
# img_format = 'jpeg'

links = [('Example link', 'http://example.org'),
         ('Another link', 'http://example.org')]

files_to_copy = (('../watermark.png', 'watermark.png'),)

plugins = [
    'sigal.plugins.adjust',
    'sigal.plugins.copyright',
    'sigal.plugins.extended_caching',
    'sigal.plugins.feeds',
    'sigal.plugins.nomedia',
    'sigal.plugins.watermark',
    'sigal.plugins.zip_gallery',
]
copyright = '© An example copyright message'
adjust_options = {'color': 0.9, 'brightness': 1.0,
                  'contrast': 1.0, 'sharpness': 0.0}
watermark = 'watermark.png'
watermark_position = (10, 10)
watermark_opacity = 0.3

theme = 'colorbox'
thumb_size = (200, 150)

rss_feed = {'feed_url': 'http://127.0.0.1:8000/feed.rss', 'nb_items': 10}
atom_feed = {'feed_url': 'http://127.0.0.1:8000/feed.atom', 'nb_items': 10}

# theme = 'photoswipe'
# theme = 'galleria'
# thumb_size = (280, 210)
# galleria_theme = 'folio'
# show_map = True
