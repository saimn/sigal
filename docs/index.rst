=======
 Sigal
=======

Sigal is yet another simple static gallery generator. It's written in Python
and it allows to build a static gallery of images with the following features:

* process directories recursively,
* resize images and create thumbnails,
* generate html pages using jinja2 templates,
* relative links for a portable output,
* MIT licensed.

Links

* Latest documentation on `readthedocs.org`_
* Source, issues and pull requests on `Github`_
* Releases on `PyPI`_

.. _readthedocs.org: http://sigal.rtfd.org/
.. _Github: https://github.com/saimn/sigal/
.. _PyPI: http://pypi.python.org/pypi/sigal

Installation
------------

Install the extension with one of the following commands::

    $ easy_install sigal

or alternatively if you have pip installed::

    $ pip install sigal

Dependencies
~~~~~~~~~~~~

- Python Imaging Library (PIL / Pillow)
- Jinja2
- Python Markdown
- pyexiv2 (optionnal, used to copy exif metadatas)

How to Use
----------

::

    $ sigal [-h] [--version] [-f] input_dir output_dir

Required arguments:

``input_dir``
  input directory

``output_dir``
  output directory

Optional arguments:

``-h|--help``
  Show this help message and exit

``--version``
  Show program's version number and exit

``-f|--force``
  Force the reprocessing of existing images and thumbnails

``-v, --verbose``
  Show all messages

``-d, --debug``
  Show all message, including debug messages


Configuration
-------------

The configuration for the gallery must be set in ``<input_dir>/sigal.conf``.
An example file with explanations on the settings is available in
``tests/sample/sigal.conf`` and is shown below:

.. literalinclude:: ../tests/sample/sigal.conf
   :language: ini


Album information
-----------------

Information on an album can be given in a file using the markdown syntax,
named `index.mkd` ::

    Title: Another example gallery
    Representative: test2.jpg

    And a *cool* description.

If this file does not exist the directory's name is used for the title, and
the first image of the directory is used as representative.


Credits
-------

* galleria: http://galleria.aino.se/
* WordPress Photography Theme: http://thethemefoundry.com/photography/


Changelog
---------

Version 0.1
~~~~~~~~~~~

Released on 2012-05-13.

First public release.
