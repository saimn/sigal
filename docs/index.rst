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

To get started, just run ``sigal init`` which will copy an example
configuration file in the current directory. All configuration values have a
default; values that are commented out serve to show the default. Default
values are specified when modified in this example config file.

After adapting the configuration to your needs, put your images in a
sub-directory and run ``sigal build <your images directory>``. The next time
you run ``sigal build``, only the new images will be processed. Use the ``-f``
flag to force the reprocessing of all the images.

To visualize your gallery, you can either use ``sigal serve`` which runs a
basic web server, or you can use the ``index_in_url = True`` setting which
will add ``index.html`` to the urls to allow browsing without the server.


Help of the ``sigal build`` command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ sigal build [-h] [-d] [-v] [-f] [-c CONFIG] [-t THEME]
            input_dir [output_dir]

Required arguments:

``input_dir``
  Input directory

Optional arguments:

``output_dir``
  Output directory (default: ``_build/``)

``-h|--help``
  Show this help message and exit

``-f|--force``
  Force the reprocessing of existing images and thumbnails

``-v, --verbose``
  Show all messages

``-d, --debug``
  Show all message, including debug messages

``-c CONFIG, --config CONFIG``
  Configuration file (default: ``<input_dir>/sigal.conf.py``)

``-t THEME, --theme THEME``
  Specify a theme directory, or a theme name for the themes included with Sigal


Configuration
-------------

The configuration for the gallery must be set in ``<input_dir>/sigal.conf.py``.
An example file with explanations on the settings is available in
``tests/sample/sigal.conf.py`` and is shown below:

.. literalinclude:: ../sigal/templates/sigal.conf.py
   :language: python


Album information
-----------------

Information on an album can be given in a file using the markdown syntax,
named ``index.md`` :

::

    Title: Another example gallery
    Thumbnail: test2.jpg

    And a *cool* description.

If this file does not exist the directory's name is used for the title, and
the first image of the directory is used as thumbnail.


Changelog
---------

Version 0.3
~~~~~~~~~~~

Released on 2013-xx-xx.

- Fix packaging issues.
- Add a setting to optionally add `index.html` to the URLs.
- Add a setting to specify a list of links and adapt the themes to show the
  links.
- Use EXIF info to fix orientation.
- Replace the ``jpg_quality`` setting with a dict of options.
- Manage directories with only sub-directories and add some checks.
- Change the command-line interface to use sub-commands: ``init``, ``build``
  and ``serve``.

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
