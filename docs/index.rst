=======================================
Sigal - Simple Static Gallery Generator
=======================================

Sigal is yet another simple static gallery generator. It's written in Python
and it allows to build a static gallery of images with the following features:

* Process directories recursively.
* Generate HTML pages using jinja2 templates.
* Relative links for a portable output.
* Themes support.
* MIT licensed.

The idea behind Sigal is to ease the use of the javascript librairies like
`galleria`_. These librairies do a great job to display the images, Sigal does
what is missing: resize images, create thumbnails, generate html pages.

Sigal is currently compatible only with python 2.

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

- Argh
- Clint
- Jinja2
- Pilkit
- Python Imaging Library (PIL / Pillow)
- Python Markdown


How to Use
----------

Init
  To get started, just run ``sigal init`` which will copy an example
  configuration file in the current directory. All configuration values have a
  default; values that are commented out serve to show the default. Default
  values are specified when modified in this example config file.

Build
  After adapting the configuration to your needs, put your images in a
  sub-directory and run ``sigal build <your images directory>``. The next time
  you run ``sigal build``, only the new images will be processed. Use the
  ``-f`` flag to force the reprocessing of all the images.

Serve
  To visualize your gallery, you can use ``sigal serve`` which runs a basic
  web server. This server should only be used for local browsing, not in
  production. Another option is to use the ``index_in_url = True`` setting,
  which will add ``index.html`` to the urls to allow browsing without a
  server.


Help of the ``sigal build`` command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ sigal build [-h] [-d] [-v] [-f] [-c CONFIG] [-t THEME]
            [source] [destination]

Required arguments:

``source``
  Input directory

``destination``
  Output directory (default: ``_build/``)

Optional arguments:

``-h, --help``
  Show this help message and exit

``-f, --force``
  Force the reprocessing of existing images and thumbnails

``-v, --verbose``
  Show all messages

``-d, --debug``
  Show all message, including debug messages

``-c CONFIG, --config CONFIG``
  Configuration file (default: ``sigal.conf.py`` in the current working
  directory)

``-t THEME, --theme THEME``
  Specify a theme directory, or a theme name for the themes included with Sigal


Configuration
-------------

The configuration must be set in a ``sigal.conf.py`` file in the current
directory. It can also be specified with the ``-c`` flag. An example file with
explanations on the settings is available in ``sigal/templates/sigal.conf.py``
and is shown below. This file is copied to the current directory with the
``sigal init`` commmand.

.. literalinclude:: ../sigal/templates/sigal.conf.py
   :language: python


Album information
-----------------

Information on an album can be given in a file using the `markdown`_ syntax,
named ``index.md`` :

::

    Title: Another example gallery
    Thumbnail: test2.jpg

    And a description with *Markdown* syntax.

Some meta-data keys are used by Sigal to get the useful informations on the
gallery:

- *Title*: the gallery title.
- *Thumbnail*: the thumbnail that will be used in the parent directory to
  represent the gallery.

Any additional meta-data is available in the templates. For instance::

    Authors: Waylan Limberg
             John Doe

can be used in the template with:

.. code-block:: jinja

    {% if 'authors' in meta %}
    <p>Authors: {{ meta.authors|join(', ') }}</>
    {% endif %}

If this file does not exist or if some meta-data is missing:

- The directory's name is used for the title (dashes and underscores are
  replaced with spaces).
- The first image of the directory is used as thumbnail.

.. _markdown: http://daringfireball.net/projects/markdown/


Changelog
---------

Version 0.4.1
~~~~~~~~~~~~~

Released on 2013-07-19.

- Fix a bug with unicode paths and filenames.
- Update colorbox to 1.4.26
- Add links to the original images.

Version 0.4.0
~~~~~~~~~~~~~

Released on 2013-06-12.

- Add a setting to disable the writing of HTML files.
- Use Pilkit.
- Remove multiprocessing.
- Add new settings for the source and destination directories.
- All meta-data are available in the templates.
- Galleria theme is now responsive
- Add a setting to choose the pilkit processor used to resize the images.

Version 0.3.3
~~~~~~~~~~~~~

Released on 2013-03-20.

- Catch exception when PIL fails to read the exif metadata.

Version 0.3.2
~~~~~~~~~~~~~

Released on 2013-03-14.

- Bugfix for PNG files which don't have exif metadata.
- Move unit tests to py.test.
- Fix images path in colorbox theme.
- Group package meta in a module.

Version 0.3.1
~~~~~~~~~~~~~

Released on 2013-03-11.

- Fix the path of the sample config file (which was not included in the
  previous release).

Version 0.3
~~~~~~~~~~~

Released on 2013-03-04.

- Fix packaging issues.
- New setting ``index_in_url`` to optionally add `index.html` to the URLs.
- New setting ``links`` to specify a list of links.
- Use EXIF info to fix orientation.
- Replace the ``jpg_quality`` setting with a dict of options.
- Manage directories with only sub-directories and add some checks.
- Change the command-line interface to use sub-commands: ``init``, ``build``
  and ``serve``.
- Parallel processing.

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
