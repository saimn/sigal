=======
 Sigal
=======

Sigal is yet another simple static gallery generator. It's written in Python
and it allows to build a static gallery of images with the following features:

* process directories recursively,
* resize images and create thumbnails,
* generate HTML pages using jinja2 templates,
* relative links for a portable output,
* MIT licensed.

Links :

* Latest documentation on the `website`_
* Source, issues and pull requests on `Github`_
* Releases on `PyPI`_

.. _website: http://sigal.saimon.org/
.. _Github: https://github.com/saimn/sigal/
.. _PyPI: http://pypi.python.org/pypi/sigal

Themes & Demo
-------------

Sigal comes with two themes, based on the `colorbox`_ and `galleria`_
Javascript libraries:

- `colorbox demo`_
- `galleria demo`_

.. _galleria: http://galleria.io/
.. _colorbox: http://www.jacklmoore.com/colorbox
.. _galleria demo: http://saimon.org/sigal-demo/galleria/
.. _colorbox demo: http://saimon.org/sigal-demo/colorbox/

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
- pyexiv2 (optional, used to copy exif metadatas)

How to Use
----------

::

    $ sigal [-h] [--version] [-f] [-v] [-d] [-c CONFIG] [-t THEME]
            input_dir [output_dir]

Required arguments:

``input_dir``
  input directory

Optional arguments:

``output_dir``
  output directory (default: ``_build/``)

``-h|--help``
  show this help message and exit

``--version``
  show program's version number and exit

``-f|--force``
  force the reprocessing of existing images and thumbnails

``-v, --verbose``
  show all messages

``-d, --debug``
  show all message, including debug messages

``-c CONFIG, --config CONFIG``
  configuration file (default: ``<input_dir>/sigal.conf.py``)

``-t THEME, --theme THEME``
  specify a theme directory, or a theme name for the themes included with Sigal


Configuration
-------------

The configuration for the gallery must be set in ``<input_dir>/sigal.conf.py``.
An example file with explanations on the settings is available in
``tests/sample/sigal.conf.py`` and is shown below:

.. literalinclude:: ../tests/sample/sigal.conf.py
   :language: python


Album information
-----------------

Information on an album can be given in a file using the markdown syntax,
named ``index.mkd`` :

::

    Title: Another example gallery
    Representative: test2.jpg

    And a *cool* description.

If this file does not exist the directory's name is used for the title, and
the first image of the directory is used as representative.

Changelog
---------


Version 0.2
~~~~~~~~~~~

Released on 2012-12-20.

- Improve the bundled themes (update galleria, new colorbox theme).
- Improve the CLI (new arguments, nicer output).
- Change the licence to MIT.
- Change the description file to a markdown syntax file.
- Change the settings file to a python file, and add more settings.

Version 0.1
~~~~~~~~~~~

Released on 2012-05-13.

First public release.
