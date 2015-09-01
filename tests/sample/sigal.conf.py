# -*- coding: utf-8 -*-

author = 'John Doe'
title = u"Sigal test gallery ☺"
source = 'pictures'
thumb_suffix = '.tn'
keep_orig = True

links = [('Example link', 'http://example.org'),
         ('Another link', 'http://example.org')]

plugins = ['sigal.plugins.adjust', 'sigal.plugins.copyright', 'sigal.plugins.watermark']
copyright = u"© An example copyright message"
adjust_options = {'color': 0.0, 'brightness': 1.0,
                  'contrast': 1.0, 'sharpness': 0.0}
watermark = "watermark.png"
watermark_position = "tile"
watermark_opacity = 0.3

theme = 'colorbox'
thumb_size = (200, 150)

# theme = 'galleria'
# thumb_size = (280, 210)
# show_map = True
