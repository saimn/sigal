Sigal - Simple Static Gallery Generator
=======================================

.. image:: https://secure.travis-ci.org/saimn/sigal.png?branch=master
   :target: https://travis-ci.org/saimn/sigal
   :alt: Travis-ci: continuous integration status.

.. image:: https://codecov.io/gh/saimn/sigal/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/saimn/sigal
   :alt: codecov.io

Sigal is yet another simple static gallery generator. It's written in Python
and it allows to build a static gallery of images with the following features:

* Process directories recursively.
* Generate HTML pages using jinja2 templates.
* Relative links for a portable output.
* Support themes, videos, EXIF tags, zip download.
* Parallel processing.
* MIT licensed.

The idea behind Sigal is to ease the use of the javascript libraries like
galleria_. These libraries do a great job to display the images, Sigal does
what is missing: resize images, create thumbnails, generate HTML pages.

Sigal is compatible with Python 3.5+.

Links :

* Latest documentation on the website_
* Source, issues and pull requests on GitHub_
* Releases on PyPI_
* ``#sigal`` on Freenode, or with the webchat_ interface.
* `Mailing list`_ at Librelist (Archives_).

Themes & Demo
-------------

Sigal comes with three themes, based on the colorbox_, galleria_ and photoswipe_
Javascript libraries:

- `colorbox demo`_
- `galleria demo`_
- `photoswipe demo`_

.. _website: http://sigal.saimon.org/
.. _GitHub: https://github.com/saimn/sigal/
.. _PyPI: http://pypi.python.org/pypi/sigal
.. _galleria: http://galleria.io/
.. _colorbox: http://www.jacklmoore.com/colorbox
.. _photoswipe: http://photoswipe.com
.. _galleria demo: http://saimon.org/sigal-demo/galleria/
.. _colorbox demo: http://saimon.org/sigal-demo/colorbox/
.. _photoswipe demo: http://saimon.org/sigal-demo/photoswipe/
.. _webchat: http://webchat.freenode.net/?channels=sigal
.. _Archives: http://librelist.com/browser/sigal/
.. _Mailing list: mailto:sigal@librelist.com
