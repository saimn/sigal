Sigal - Simple Static Gallery Generator
=======================================

.. image:: https://secure.travis-ci.org/saimn/sigal.png?branch=master
   :target: https://travis-ci.org/saimn/sigal
   :alt: Travis-ci: continuous integration status.

Sigal is yet another simple static gallery generator. It's written in Python
and it allows to build a static gallery of images with the following features:

* Process directories recursively.
* Generate HTML pages using jinja2 templates.
* Relative links for a portable output.
* Support themes, videos, EXIF tags, zip download.
* Parallel processing.
* MIT licensed.

The idea behind Sigal is to ease the use of the javascript librairies like
galleria_. These librairies do a great job to display the images, Sigal does
what is missing: resize images, create thumbnails, generate html pages.

Sigal is compatible with Python 2.7 and 3.3.

Links :

* Latest documentation on the website_
* Source, issues and pull requests on Github_
* Releases on PyPI_
* ``#sigal`` on Freenode, or with the webchat_ interface.
* `Mailing list`_ at Librelist (Archives_).

Themes & Demo
-------------

Sigal comes with two themes, based on the colorbox_ and galleria_
Javascript libraries:

- `colorbox demo`_
- `galleria demo`_

.. _website: http://sigal.saimon.org/
.. _Github: https://github.com/saimn/sigal/
.. _PyPI: http://pypi.python.org/pypi/sigal
.. _galleria: http://galleria.io/
.. _colorbox: http://www.jacklmoore.com/colorbox
.. _galleria demo: http://saimon.org/sigal-demo/galleria/
.. _colorbox demo: http://saimon.org/sigal-demo/colorbox/
.. _webchat: http://webchat.freenode.net/?channels=sigal
.. _Archives: http://librelist.com/browser/sigal/
.. _Mailing list: mailto:sigal@librelist.com
